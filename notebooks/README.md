# Thực hành bằng Jupyter Notebook

Mở **[00_Gamer_Behavior_Clustering.ipynb](00_Gamer_Behavior_Clustering.ipynb)** để xem toàn bộ bài theo từng bước. File đã lưu bảng và hình từ lần chạy thật, có thể xem trên GitHub hoặc VS Code mà không cần chạy lại ngay.

## Mở trong VS Code

1. Mở thư mục `gamer_profiling`, cài extension **Python** và **Jupyter** của Microsoft nếu máy chưa có.
2. Từ terminal ở thư mục dự án, cài thư viện:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements-notebook.txt
   ```

   Nếu dùng môi trường đã có ở thư mục cha như bản dự án ban đầu, dùng `..\.venv\Scripts\python.exe` thay cho `.\.venv\Scripts\python.exe`.

3. Mở notebook `00`, bấm **Select Kernel → Python Environments**, chọn đúng `.venv` vừa cài thư viện.
4. Chọn **Restart Kernel**, sau đó **Run All**. Chạy từng ô thì dùng **Shift+Enter**, theo thứ tự từ trên xuống.

JupyterLab cũng mở được các file này nếu máy đã cài. Linux/macOS dùng `.venv/bin/python` thay cho đường dẫn Windows.

## Tám notebook theo công đoạn

| File | Nội dung | Tệp trung gian cần có |
|---|---|---|
| [01_data_understanding.ipynb](01_data_understanding.ipynb) | Nguồn, từ điển cột, yêu cầu đo được và phần thiếu | Không |
| [02_statistics_eda.ipynb](02_statistics_eda.ipynb) | Thống kê, histogram, boxplot, tương quan và thời lượng | Không |
| [03_data_cleaning.ipynb](03_data_cleaning.ipynb) | Ép kiểu, thiếu ẩn, âm/vô cực, ID trùng, ngoại lệ IQR | Không |
| [04_data_transformation.ipynb](04_data_transformation.ipynb) | Chia train/holdout, imputer, StandardScaler | Không |
| [05_clustering.ipynb](05_clustering.ipynb) | Ward, K-Means, tâm khởi tạo, chọn k | Chạy 04 trước |
| [06_model_evaluation.ipynb](06_model_evaluation.ipynb) | Silhouette/DBI holdout, ổn định ARI, bỏ PlayTimeHours | Chạy 04–05 trước |
| [07_player_profiling.ipynb](07_player_profiling.ipynb) | Hồ sơ cụm, heatmap, PCA, đối chiếu engagement | Chạy 04–06 trước |
| [08_prediction_strategy.ipynb](08_prediction_strategy.ipynb) | Gán người mới, giả thuyết chiến lược, kiểm chứng số liệu | Chạy 04–07 trước |

Mỗi file có ô khởi tạo riêng nên có thể dùng kernel mới; các bước 05–08 đọc tệp do bước trước tạo. Để chạy tuần tự cả tám phần trong một file không phải quản lý tệp thủ công, dùng notebook `00`.

## Số liệu và khả năng tái lập

- Notebook đọc cùng CSV Kaggle và dùng cùng seed, cách lấy mẫu, đặc trưng và thuật toán với `gamer_clustering.py`.
- Chọn k trên mẫu train; fit imputer/scaler trên train; holdout chỉ dùng đánh giá sau khóa k.
- Mỗi biểu đồ được tạo bằng code ngay trong ô và hiển thị bên dưới, gồm cả boxplot như ảnh tham khảo.
- Sản phẩm thực hành mới nằm trong `outputs/notebook/`, được Git bỏ qua. Chạy notebook không ghi đè bộ kết quả báo cáo hiện có trong `outputs/`.
- Cuối phần 08 có đối chiếu bằng assertion với bảng chọn k, holdout, hồ sơ, ổn định, độ nhạy và nhãn đã dùng trong báo cáo. File tổng kết chạy kiểm tra nằm ở [outputs/notebook_verification.json](../outputs/notebook_verification.json).
- Số hiệu cụm có thể thay đổi khi đổi phiên bản thư viện, seed hoặc dữ liệu; dùng đúng requirements để tái lập kết quả đã nộp. Cần kiểm tra lại báo cáo khi đổi thiết kế, không bỏ assertion chỉ để che chênh lệch.

## Tạo lại và chạy kiểm tra cả bộ

```powershell
.\.venv\Scripts\python.exe build_notebooks.py
.\.venv\Scripts\python.exe execute_notebooks.py
```

`build_notebooks.py` tạo lại nội dung notebook và xóa output cũ trong các file được tạo. `execute_notebooks.py` chạy từng file bằng kernel mới của chính Python đang dùng, lưu output thật và kiểm tra tính nhất quán. Chỉ chạy bản tổng hợp bằng `execute_notebooks.py --only-main`.

## Cách trình bày trước lớp

Mở notebook `00`, thu gọn các phần chưa nói, rồi lần lượt giải thích: vấn đề → code → bảng/hình → nhận xét. Không cần chạy lại toàn bộ mô hình giữa lúc thuyết trình nếu đã kiểm tra trước; output đã được lưu sẵn. Nếu thầy yêu cầu thực thi, dùng kernel đã chuẩn bị và chạy theo thứ tự.

Dữ liệu nguồn được tác giả xác nhận là **synthetic**. Không có wins/losses, vật phẩm theo thời gian, Elo/MMR hoặc số tiền mua. Kết quả không xác nhận nhóm High-Spenders và chưa chứng minh tăng doanh thu. Các giới hạn này được nêu trong cả notebook và báo cáo.
