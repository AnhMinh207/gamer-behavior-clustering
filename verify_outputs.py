"""Kiểm chứng kết quả, chia dữ liệu và gán người mới, không huấn luyện lại."""
from pathlib import Path
import json
import hashlib
import zipfile
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.model_selection import train_test_split
from threadpoolctl import threadpool_limits
from lxml import etree
from gamer_clustering import clean_features, choose_k

R=Path(__file__).resolve().parent; O=R/'outputs'
checks=[]


def check(condition, name):
    if not condition: raise AssertionError(name)
    checks.append(name)


def main():
    s=json.loads((O/'summary.json').read_text(encoding='utf-8'))
    df=pd.read_csv(R/'data/online_gaming_behavior_dataset.csv')
    source_hash=hashlib.sha256((R/'data/online_gaming_behavior_dataset.csv').read_bytes()).hexdigest()
    check(source_hash==s['data_sha256'],'CSV nguyên bản khớp SHA-256')
    assignments=pd.read_csv(O/'player_assignments.csv')
    profile=pd.read_csv(O/'cluster_profiles.csv')
    split=pd.read_csv(O/'split.csv')
    train,test=train_test_split(np.arange(len(df)),test_size=.2,random_state=42)
    check(set(split[split.split=='train'].PlayerID)==set(df.iloc[train].PlayerID),'Split train tái lập đúng seed')
    check(set(split[split.split=='holdout'].PlayerID)==set(df.iloc[test].PlayerID),'Split holdout tái lập đúng seed')
    check(not(set(df.iloc[train].PlayerID)&set(df.iloc[test].PlayerID)),'Train và holdout không giao nhau theo ID')
    art=joblib.load(O/'player_cluster_model.joblib')
    x=clean_features(df)
    # Dữ liệu hiện tại không thiếu; scaler phải khớp trung bình riêng train.
    np.testing.assert_allclose(art['preprocessor'].named_steps['scaler'].mean_,x.iloc[train].mean().to_numpy())
    check(True,'Scaler khớp thống kê train, không fit toàn bộ dữ liệu')
    check('EngagementLevel' not in art['features'] and 'PlayerID' not in art['features'] and 'InGamePurchases' not in art['features'],'Không học ID, EngagementLevel hay cờ mua hàng')
    z=art['preprocessor'].transform(x)
    labels=art['model'].predict(z)
    check(np.array_equal(assignments.cluster.to_numpy(),labels),'Nhãn 40.034 người khớp predict từ mô hình đã lưu')
    check(int(profile['count'].sum())==len(df),'Tổng quy mô các cụm bằng số dòng dữ liệu')
    for row in profile.itertuples():
        sub=df[labels==row.cluster]
        for f in art['features']: np.testing.assert_allclose(getattr(row,f),sub[f].mean(),rtol=1e-10)
        np.testing.assert_allclose(row.purchase_rate,sub.InGamePurchases.mean())
    check(True,'Trung bình đặc trưng và tỷ lệ mua của mọi cụm khớp dữ liệu gốc')
    search=pd.read_csv(O/'model_selection.csv')
    check(len(search)==21,'Có đủ 3 phương pháp × 7 giá trị k')
    for method,k in s['selected_k'].items():
        check(choose_k(search[search.method==method])==k,f'k {method} khớp quy tắc chọn từ train')
    rng=np.random.default_rng(42)
    sub=rng.choice(len(train),s['n_ward_sample'],replace=False)
    rng.choice(len(sub),s['n_silhouette_train'],replace=False)
    ei=rng.choice(len(test),s['n_silhouette_holdout'],replace=False)
    zz=z[test]; ll=labels[test]
    target=[r for r in s['holdout'] if r['method']=='Ward_KMeans'][0]
    np.testing.assert_allclose(silhouette_score(zz[ei],ll[ei]),target['silhouette'],atol=1e-12)
    np.testing.assert_allclose(davies_bouldin_score(zz,ll),target['davies_bouldin'],atol=1e-12)
    check(True,'Silhouette và DBI holdout được tính lại độc lập, khớp summary')
    ex=pd.read_csv(O/'prediction_examples.csv')
    example_labels = art['model'].predict(art['preprocessor'].transform(clean_features(ex)))
    check(np.array_equal(ex.cluster, example_labels), 'Ví dụ người mới khớp mô hình, không cần fit')
    for name in ['Bao_cao_Gamer_Clustering.docx','Bai_noi_va_Hoi_dap.docx','Thuyet_trinh_Gamer_Clustering.pptx']:
        with zipfile.ZipFile(R/'deliverables'/name) as archive:
            check(archive.testzip() is None,f'ZIP nội bộ hợp lệ: {name}')
            for member in archive.namelist():
                if member.endswith('.xml') or member.endswith('.rels'):
                    etree.fromstring(archive.read(member))
        check(True,f'Tất cả XML đọc được: {name}')
    from pptx import Presentation
    prs=Presentation(R/'deliverables/Thuyet_trinh_Gamer_Clustering.pptx')
    check(len(prs.slides)==18,'PowerPoint đủ 18 slide')
    for slide in prs.slides:
        check(len(slide.notes_slide.notes_text_frame.text)>300,'Slide có lời nói đầy đủ trong Notes')
        for sh in slide.shapes:
            if sh.has_text_frame:
                for pp in sh.text_frame.paragraphs:
                    for rr in pp.runs:
                        check((rr.font.name or pp.font.name)=='Arial','Chữ trên slide dùng Arial (kể cả kế thừa đoạn)')
    result={'passed':True,'checks_count':len(checks),'checks':list(dict.fromkeys(checks))}
    (O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    with threadpool_limits(limits=2): main()
