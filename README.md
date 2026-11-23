# Gamer Behavior Clustering & Player Profiling

Dự án môn Khai phá dữ liệu, viết bằng tiếng Việt. Đọc báo cáo Word trong deliverables/.

## Chạy lại

Yêu cầu Python 3.13 trên máy có thể cài các phiên bản trong requirements.txt. Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe gamer_clustering.py
.\.venv\Scripts\python.exe build_deliverables.py
```

Linux/macOS dùng `.venv/bin/python` thay cho `.\.venv\Scripts\python.exe`.
Đã chạy thực tế với Python 3.13.0; chưa xác nhận trên mọi hệ điều hành.
Từ thư mục bất kỳ có thể chạy đường dẫn tuyệt đối đến script vì dữ liệu được định vị theo __file__.

## Đầu vào và nguồn

CSV nguyên bản: data/online_gaming_behavior_dataset.csv.
Tác giả: Rabie El Kharoua, Predict Online Gaming Behavior Dataset, version 1 (2024).
Nguồn: https://www.kaggle.com/datasets/rabieelkharoua/predict-online-gaming-behavior-dataset
Giấy phép: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ . Dữ liệu được đóng gói lại cùng ghi nguồn; không thay đổi CSV nguồn.
Metadata: data/dataset_card.json và data/metadata.json. Nguồn ghi rõ **synthetic** cho giáo dục.
SHA-256 CSV: `63e63057d2984a0630d9af5457df564ac35af5ec0d9d7d82dad6a8e7097f4e15`.

Không có wins/losses, vật phẩm theo thời gian, MMR/Elo hoặc số tiền mua.
PlayerLevel = tiến trình; AchievementsUnlocked = thành tích tích lũy; InGamePurchases = 0/1.
Không thể đo tỷ lệ thắng/thua, tốc độ thu vật phẩm, kỹ năng thật hay High-Spenders từ CSV này.
PlayTimeHours và AvgSessionDurationMinutes mâu thuẫn về ngữ nghĩa nguồn; có kiểm tra độ nhạy bỏ PlayTimeHours.
Không tự sinh dữ liệu mới. Dùng đúng nguồn đề giao, công bố giới hạn dữ liệu tổng hợp.

## Thiết kế thực nghiệm

- 40,034 dòng; train 32,027, holdout 8,007; seed 42.
- Năm biến: PlayTimeHours, SessionsPerWeek, AvgSessionDurationMinutes, PlayerLevel, AchievementsUnlocked.
- Pipeline trung vị + StandardScaler fit train; không fit holdout.
- So KMeans++ (20 khởi tạo), Agglomerative Ward và Ward → tâm → KMeans.
- Chọn k=2…8 trên cùng mẫu 4,000 train bằng tổng hạng Silhouette giảm, DBI tăng; hòa ưu tiên Silhouette rồi k nhỏ.
- Chọn k riêng mỗi phương pháp. Ward_KMeans là phương pháp chính xác định trước theo đề.
- Silhouette trên cùng mẫu 2.000 trong từng giai đoạn; DBI dùng toàn bộ tập đánh giá.
- Sau khóa k, K-Means và mô hình kết hợp fit toàn train. Ward thuần gán ngoài mẫu qua tâm, không coi là Ward chính xác trên toàn dữ liệu.
- Holdout không dùng chọn k/phương pháp. Không dùng EngagementLevel để học; mua hàng chỉ phân tích sau học.
- Hồ sơ mô tả toàn bộ dữ liệu. Đổi seed mẫu Ward 5 lần, so ARI trên cùng holdout; phân tích bỏ PlayTimeHours giữ k cố định.
- PCA chỉ minh họa, không dùng học cụm.

## Gán người chơi mới

CSV mới cần đủ năm cột đầu vào; có thể có PlayerID và cột khác.

```powershell
.\.venv\Scripts\python.exe gamer_clustering.py --predict nguoi_choi_moi.csv
```

Tạo nguoi_choi_moi_clustered.csv bên cạnh đầu vào. Không fit lại scaler/mô hình.
Ví dụ kết quả có tại outputs/prediction_examples.csv. Chỉ mở joblib từ nguồn tin cậy.

## Tệp bàn giao

- gamer_clustering.py: một tệp thực hiện phân tích từ đầu đến cuối.
- build_deliverables.py: tạo Word, PPTX và bài nói từ kết quả thật.
- outputs/model_selection.csv: 21 cấu hình; holdout_metrics.csv: kết quả sau khóa k.
- outputs/cluster_profiles.csv và player_assignments.csv: hồ sơ và nhãn từng người.
- outputs/stability.csv, feature_sensitivity.json: kiểm tra độ nhạy.
- outputs/player_cluster_model.joblib, summary.json, run.log: mô hình, cấu hình, môi trường.
- outputs/figures/: tám hình minh họa thật.
- deliverables/: báo cáo, PowerPoint 18 slide có Notes, bài nói hai người và hỏi đáp.

Thông tin trường, giảng viên, lớp, thành viên/MSSV chưa được cung cấp: có chỗ điền trên bìa.
Thời lượng mặc định 13–15 phút, người 1 slide 1–7, người 2 slide 8–18.
Mở Word và Ctrl+A, F9 để cập nhật mục lục; diễn tập PowerPoint bằng F5.
Kết quả và giới hạn kiểm tra xem deliverables/KIEM_TRA_BAN_GIAO.txt.

## Tài liệu thuật toán

- https://scikit-learn.org/stable/modules/clustering.html
- https://docs.scipy.org/doc/scipy/reference/cluster.hierarchy.html

Chỉ số nội bộ chưa chứng minh hiệu quả thương mại; chiến lược trong báo cáo là giả thuyết A/B test.
