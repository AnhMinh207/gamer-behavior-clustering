"""Phân cụm người chơi. Chạy: python gamer_clustering.py [--predict FILE.csv].

Dữ liệu Kaggle tổng hợp do Rabie El Kharoua công bố, CC BY 4.0.
Không sinh dữ liệu mới và không sử dụng EngagementLevel khi học/chọn mô hình.
"""
from pathlib import Path
import argparse
import hashlib
import json
import logging
import platform
import time
import sys
import importlib.metadata
import os
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parent / 'outputs' / '.mplconfig'))
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import linkage, cut_tree, dendrogram
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import (silhouette_score, silhouette_samples, davies_bouldin_score,
                             adjusted_rand_score, pairwise_distances)
from sklearn.metrics.pairwise import pairwise_distances_argmin
from sklearn.decomposition import PCA
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
FEATURES = ['PlayTimeHours', 'SessionsPerWeek', 'AvgSessionDurationMinutes',
            'PlayerLevel', 'AchievementsUnlocked']
METHODS = ['KMeans', 'Ward', 'Ward_KMeans']
SEED = 42


def save_json(data, path):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def clean_features(df):
    """Biến đổi xác định, không ước lượng từ dữ liệu; dùng cả khi dự đoán."""
    missing = set(FEATURES) - set(df.columns)
    if missing:
        raise ValueError(f'Thiếu cột bắt buộc: {sorted(missing)}')
    x = df[FEATURES].apply(pd.to_numeric, errors='coerce')
    x = x.replace([np.inf, -np.inf], np.nan)
    return x.mask(x < 0)


def audit_data(df):
    x = clean_features(df)
    audit = {'rows': len(df), 'columns': len(df.columns),
             'duplicate_rows': int(df.duplicated().sum()),
             'duplicate_player_ids': int(df.PlayerID.duplicated().sum()),
             'raw_missing_cells': int(df.isna().sum().sum()),
             'feature_missing_after_coercion': x.isna().sum().to_dict(),
             'synthetic_source': True,
             'time_units_warning': 'PlayTimeHours mô tả giờ/phiên nhưng không khớp AvgSessionDurationMinutes/60; không diễn giải là giờ/tuần.',
             'unsupported_metrics': ['win_loss_ratio', 'item_collection_rate', 'true_skill_score', 'spend_amount']}
    time_error = (x.PlayTimeHours - x.AvgSessionDurationMinutes / 60).abs()
    audit['session_time_disagreement_rate'] = float((time_error > 0.1).mean())
    audit['session_time_pearson'] = float(x.PlayTimeHours.corr(x.AvgSessionDurationMinutes))
    df.describe(include='all').T.to_csv(OUT / 'data_summary.csv', encoding='utf-8-sig')
    x.corr().to_csv(OUT / 'feature_correlations.csv')
    pd.DataFrame({'feature': FEATURES, 'variance': x.var().values,
                  'nunique': x.nunique().values, 'missing': x.isna().sum().values}).to_csv(
                      OUT / 'feature_audit.csv', index=False)
    save_json(audit, OUT / 'data_audit.json')
    if audit['duplicate_rows'] or audit['duplicate_player_ids']:
        raise ValueError('Có dòng/PlayerID trùng: cần quyết định xử lý trước khi chia mẫu.')
    return x, audit


def centers_from_labels(x, labels):
    return np.vstack([x[labels == i].mean(axis=0) for i in np.unique(labels)])


def fit_models(x, k, tree, seed=SEED):
    """Ward (Euclidean) và tâm Ward làm khởi tạo K-Means trên cùng mẫu."""
    ward_labels = cut_tree(tree, n_clusters=k).ravel()
    ward_centers = centers_from_labels(x, ward_labels)
    km = KMeans(n_clusters=k, init='k-means++', n_init=20,
                max_iter=300, random_state=seed).fit(x)
    hybrid = KMeans(n_clusters=k, init=ward_centers, n_init=1,
                    max_iter=300, random_state=seed).fit(x)
    return {'KMeans': (km.labels_, km.cluster_centers_),
            'Ward': (ward_labels, ward_centers),
            'Ward_KMeans': (hybrid.labels_, hybrid.cluster_centers_)}


def metrics(x, labels, eval_idx, distances):
    small = labels[eval_idx]
    if len(np.unique(small)) < 2:
        raise ValueError('Mẫu Silhouette chỉ chứa một cụm.')
    return {'silhouette': float(silhouette_score(distances, small, metric='precomputed')),
            'davies_bouldin': float(davies_bouldin_score(x, labels)),
            'min_cluster_pct': float(pd.Series(labels).value_counts(normalize=True).min() * 100)}


def choose_k(table):
    """Chọn trong từng thuật toán: tổng hạng Silhouette giảm và DBI tăng."""
    t = table.copy()
    t['rank_sum'] = t.silhouette.rank(ascending=False, method='min') + t.davies_bouldin.rank(method='min')
    return int(t.sort_values(['rank_sum', 'silhouette', 'k'], ascending=[True, False, True]).iloc[0].k)


def figsave(name):
    plt.tight_layout()
    plt.savefig(OUT / 'figures' / name, dpi=180, bbox_inches='tight')
    plt.close()


def make_figures(df, x, tree, search, labels, profile, prep):
    sns.set_theme(style='whitegrid', font='Arial', context='notebook')
    fig, axes = plt.subplots(2, 3, figsize=(12, 6))
    for ax, col in zip(axes.flat, FEATURES):
        ax.hist(x[col], bins=30, color='#197c9b', edgecolor='white')
        ax.set_title(col, fontsize=10)
        ax.set_ylabel('Số người chơi')
    axes.flat[-1].axis('off')
    figsave('01_distributions.png')
    plt.figure(figsize=(7, 5))
    sns.heatmap(x.corr(), annot=True, fmt='.2f', cmap='vlag', vmin=-1, vmax=1)
    figsave('02_correlations.png')
    plt.figure(figsize=(10, 4))
    dendrogram(tree, truncate_mode='lastp', p=24, show_leaf_counts=True)
    plt.title('Cây Ward rút gọn trên mẫu huấn luyện (24 nhánh cuối)')
    plt.ylabel('Khoảng cách gộp Ward'); plt.xlabel('Nhánh; số trong ngoặc là số quan sát')
    figsave('03_dendrogram.png')
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for method, g in search.groupby('method'):
        axes[0].plot(g.k, g.silhouette, 'o-', label=method)
        axes[1].plot(g.k, g.davies_bouldin, 'o-', label=method)
    axes[0].set_title('Silhouette: cao hơn tốt hơn')
    axes[1].set_title('Davies–Bouldin: thấp hơn tốt hơn')
    for ax in axes: ax.set_xlabel('Số cụm k'); ax.legend(fontsize=8)
    figsave('04_model_selection.png')
    z = prep.transform(x)
    pc = PCA(n_components=2).fit(z)
    xy = pc.transform(z)
    idx = np.random.default_rng(SEED).choice(len(x), min(7000, len(x)), replace=False)
    plt.figure(figsize=(8, 5))
    plt.scatter(xy[idx, 0], xy[idx, 1], c=labels[idx], cmap='tab10', s=6, alpha=.35)
    plt.xlabel('PC1'); plt.ylabel('PC2')
    plt.title(f'Chiếu PCA 2D: {pc.explained_variance_ratio_.sum():.1%} phương sai; chỉ để minh họa')
    figsave('05_pca.png')
    means = profile[FEATURES]
    normalized = (means - x.mean()) / x.std(ddof=0)
    plt.figure(figsize=(10, max(3, .65 * len(profile))))
    sns.heatmap(normalized, annot=True, fmt='.2f', cmap='vlag', center=0,
                yticklabels=[f'C{int(r.cluster)}: {r.profile}' for r in profile.itertuples()])
    plt.title('Hồ sơ cụm: trung bình chuẩn hóa theo toàn bộ dữ liệu')
    figsave('06_profiles.png')
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(profile.cluster.astype(str), profile['count'], color='#197c9b')
    axes[0].set_title('Số người mỗi cụm'); axes[0].set_xlabel('Cụm')
    axes[1].bar(profile.cluster.astype(str), profile.purchase_rate * 100, color='#de9f37')
    axes[1].set_ylim(0, 100); axes[1].set_title('Có mua hàng (%); không phải mức chi tiêu')
    axes[1].set_xlabel('Cụm')
    figsave('07_sizes_purchases.png')
    # Silhouette trên cùng mẫu chỉ số của bộ dữ liệu đầy đủ, không dùng để chọn k.
    si = np.random.default_rng(SEED).choice(len(z), min(2000, len(z)), replace=False)
    vals = silhouette_samples(z[si], labels[si])
    plt.figure(figsize=(8, 5)); start = 0
    for c in sorted(np.unique(labels)):
        v = np.sort(vals[labels[si] == c]); end = start + len(v)
        plt.fill_betweenx(np.arange(start, end), 0, v, alpha=.65, label=f'Cụm {c}')
        start = end + 12
    plt.axvline(vals.mean(), color='black', linestyle='--')
    plt.xlabel('Silhouette'); plt.ylabel('Quan sát được sắp xếp trong từng cụm')
    plt.legend(); figsave('08_silhouette.png')
    return float(pc.explained_variance_ratio_.sum())


def profile_clusters(df, labels):
    d = df.copy(); d['cluster'] = labels
    p = d.groupby('cluster')[FEATURES].mean()
    p['count'] = d.groupby('cluster').size()
    p['share_pct'] = p['count'] / len(d) * 100
    p['purchase_rate'] = d.groupby('cluster').InGamePurchases.mean()
    # Hồ sơ tương đối dựa trên dữ liệu; không ép thành Casual/Hardcore/High-Spenders.
    duration_ranks = p.AvgSessionDurationMinutes.rank(pct=True)
    frequency_ranks = p.SessionsPerWeek.rank(pct=True)
    names = []
    for c in p.index:
        freq = 'Chơi thường xuyên' if frequency_ranks[c] > .5 else 'Chơi ít phiên'
        dur = 'phiên dài' if duration_ranks[c] > .5 else 'phiên ngắn'
        names.append(f'{freq}, {dur}')
    p['profile'] = names
    p = p.reset_index()
    p.to_csv(OUT / 'cluster_profiles.csv', index=False, encoding='utf-8-sig')
    d.to_csv(OUT / 'player_assignments.csv', index=False, encoding='utf-8-sig')
    pd.crosstab(d.cluster, d.EngagementLevel, normalize='index').to_csv(OUT / 'engagement_posthoc.csv')
    return p


def run(sample_size=4000, silhouette_size=2000):
    OUT.mkdir(exist_ok=True); (OUT / 'figures').mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                        handlers=[logging.FileHandler(OUT / 'run.log', mode='w', encoding='utf-8'),
                                  logging.StreamHandler(sys.stdout)])
    start = time.perf_counter()
    source = ROOT / 'data' / 'online_gaming_behavior_dataset.csv'
    df = pd.read_csv(source)
    x, audit = audit_data(df)
    train_idx, test_idx = train_test_split(np.arange(len(df)), test_size=.2, random_state=SEED)
    pd.DataFrame({'PlayerID': df.PlayerID, 'split': np.where(np.isin(np.arange(len(df)), train_idx), 'train', 'holdout')}).to_csv(OUT / 'split.csv', index=False)
    prep = Pipeline([('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())])
    ztrain = prep.fit_transform(x.iloc[train_idx]); ztest = prep.transform(x.iloc[test_idx])
    rng = np.random.default_rng(SEED)
    sub = rng.choice(len(ztrain), min(sample_size, len(ztrain)), replace=False)
    xs = ztrain[sub]
    pd.DataFrame({'PlayerID': df.iloc[train_idx[sub]].PlayerID}).to_csv(OUT / 'ward_sample_ids.csv', index=False)
    ei = rng.choice(len(xs), min(silhouette_size, len(xs)), replace=False)
    distances = pairwise_distances(xs[ei])
    tree = linkage(xs, method='ward', metric='euclidean')
    np.save(OUT / 'ward_linkage.npy', tree)
    rows, stored = [], {}
    for k in range(2, 9):
        logging.info('So sánh k=%s trên %s người, cùng mẫu/cùng không gian', k, len(xs))
        models = fit_models(xs, k, tree)
        for method, (labels, centers) in models.items():
            stored[(method, k)] = centers
            rows.append({'method': method, 'k': k, **metrics(xs, labels, ei, distances)})
    search = pd.DataFrame(rows)
    search.to_csv(OUT / 'model_selection.csv', index=False)
    selected = {m: choose_k(search[search.method == m]) for m in METHODS}
    # Không dùng holdout để chọn mô hình hay k. Đánh giá ba phương pháp đã khóa.
    test_ei = rng.choice(len(ztest), min(silhouette_size, len(ztest)), replace=False)
    test_dist = pairwise_distances(ztest[test_ei])
    evaluations, fitted = [], {}
    for method in METHODS:
        k = selected[method]
        if method == 'Ward':
            centers = stored[(method, k)]
            test_labels = pairwise_distances_argmin(ztest, centers)
            train_labels = pairwise_distances_argmin(ztrain, centers)
            model = None
        else:
            init = 'k-means++' if method == 'KMeans' else stored[('Ward', k)]
            model = KMeans(n_clusters=k, init=init, n_init=20 if method == 'KMeans' else 1,
                           max_iter=300, random_state=SEED).fit(ztrain)
            centers = model.cluster_centers_
            test_labels, train_labels = model.predict(ztest), model.labels_
        fitted[method] = (model, centers)
        evaluations.append({'method': method, 'k': k,
                            'evaluation': 'holdout_centroid_extension' if method == 'Ward' else 'holdout_predict',
                            **metrics(ztest, test_labels, test_ei, test_dist)})
    evaluation = pd.DataFrame(evaluations)
    evaluation.to_csv(OUT / 'holdout_metrics.csv', index=False)
    # Bài toán yêu cầu phương pháp kết hợp; khóa lựa chọn Ward_KMeans từ trước.
    method, k = 'Ward_KMeans', selected['Ward_KMeans']
    model, centers = fitted[method]
    all_labels = model.predict(prep.transform(x))
    profile = profile_clusters(df, all_labels)
    artifact = {'preprocessor': prep, 'model': model, 'features': FEATURES,
                'method': method, 'cluster_names': profile.set_index('cluster')['profile'].to_dict(),
                'seed': SEED, 'data_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    joblib.dump(artifact, OUT / 'player_cluster_model.joblib')
    example = df.iloc[test_idx[:5]][['PlayerID'] + FEATURES].copy()
    example['cluster'] = model.predict(prep.transform(clean_features(example)))
    example['profile'] = example.cluster.map(artifact['cluster_names'])
    example.to_csv(OUT / 'prediction_examples.csv', index=False, encoding='utf-8-sig')
    # Kiểm tra ổn định khi lấy lại mẫu Ward trên train, dự đoán cùng bộ holdout.
    ref_labels = model.predict(ztest)
    stability = []
    for seed in [7, 21, 84, 123, 2026]:
        si = np.random.default_rng(seed).choice(len(ztrain), len(xs), replace=False)
        zz = ztrain[si]
        tr = linkage(zz, method='ward')
        wl = cut_tree(tr, n_clusters=k).ravel()
        init = centers_from_labels(zz, wl)
        m = KMeans(n_clusters=k, init=init, n_init=1, random_state=seed, max_iter=300).fit(ztrain)
        lab = m.predict(ztest)
        stability.append({'seed': seed, 'ari_vs_seed42': adjusted_rand_score(ref_labels, lab),
                          **metrics(ztest, lab, test_ei, test_dist)})
    stability = pd.DataFrame(stability)
    stability.to_csv(OUT / 'stability.csv', index=False)
    # Thay đổi feature: loại PlayTimeHours có vấn đề ngữ nghĩa, chỉ báo cáo độ nhạy.
    keep = [i for i, f in enumerate(FEATURES) if f != 'PlayTimeHours']
    alt_tree = linkage(xs[:, keep], method='ward')
    alt_lab = cut_tree(alt_tree, n_clusters=k).ravel()
    alt = KMeans(n_clusters=k, init=centers_from_labels(xs[:, keep], alt_lab), n_init=1,
                 max_iter=300, random_state=SEED).fit(ztrain[:, keep])
    alt_pred = alt.predict(ztest[:, keep])
    alt_metrics = metrics(ztest[:, keep], alt_pred, test_ei, pairwise_distances(ztest[test_ei][:, keep]))
    sensitivity = {'excluded': 'PlayTimeHours', 'k_fixed': k,
                   'ari_vs_main': float(adjusted_rand_score(ref_labels, alt_pred)), **alt_metrics,
                   'note': 'Không gian khác nhau; không dùng Silhouette/DBI này để xếp hạng trực tiếp với mô hình chính.'}
    save_json(sensitivity, OUT / 'feature_sensitivity.json')
    pca_ratio = make_figures(df, x, tree, search, all_labels, profile, prep)
    versions = {p: importlib.metadata.version(p) for p in ['numpy','pandas','scipy','scikit-learn','matplotlib','seaborn','joblib','threadpoolctl','python-docx','python-pptx','pillow']}
    summary = {'data_sha256': artifact['data_sha256'], 'seed': SEED, 'rows': len(df),
               'n_train': len(train_idx), 'n_holdout': len(test_idx), 'n_ward_sample': len(xs),
               'n_silhouette_train': len(ei), 'n_silhouette_holdout': len(test_ei),
               'features': FEATURES, 'selected_k': selected, 'final_method': method,
               'final_k': k, 'holdout': evaluation.to_dict(orient='records'),
               'stability_ari_mean': float(stability.ari_vs_seed42.mean()),
               'stability_ari_min': float(stability.ari_vs_seed42.min()),
               'feature_sensitivity': sensitivity, 'pca_2d_variance': pca_ratio,
               'profile_population': 'all_rows; model fit on train only',
               'runtime_seconds': round(time.perf_counter() - start, 2),
               'python': platform.python_version(), 'versions': versions}
    save_json(summary, OUT / 'summary.json')
    (ROOT / 'requirements.txt').write_text('\n'.join(f'{p}=={v}' for p,v in versions.items()) + '\n', encoding='utf-8')
    logging.info('Hoàn tất: %s', json.dumps(summary, ensure_ascii=False))


def predict(path):
    artifact = joblib.load(OUT / 'player_cluster_model.joblib')
    df = pd.read_csv(path)
    z = artifact['preprocessor'].transform(clean_features(df))
    df['cluster'] = artifact['model'].predict(z)
    df['profile'] = df.cluster.map(artifact['cluster_names'])
    dest = path.with_name(path.stem + '_clustered.csv')
    df.to_csv(dest, index=False, encoding='utf-8-sig')
    print(dest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predict', type=Path)
    parser.add_argument('--sample-size', type=int, default=4000)
    parser.add_argument('--silhouette-size', type=int, default=2000)
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        if args.predict: predict(args.predict)
        else: run(args.sample_size, args.silhouette_size)
