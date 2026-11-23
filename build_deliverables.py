"""Tạo Word, PowerPoint và lời thuyết trình từ outputs/summary.json thực tế."""
from pathlib import Path
import json
import pandas as pd
from docx import Document
from docx.shared import Inches as DInches, Pt as DPt, RGBColor as DColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement as PX

ROOT = Path(__file__).resolve().parent
O = ROOT / 'outputs'
D = ROOT / 'deliverables'
NAVY = '12283F'; TEAL = '127F8C'; GOLD = 'D99A32'; INK = '22384B'; GRAY = '607284'
SOURCE = 'https://www.kaggle.com/datasets/rabieelkharoua/predict-online-gaming-behavior-dataset'
DOCS = 'https://scikit-learn.org/stable/modules/clustering.html'


def field(paragraph, instruction):
    r = paragraph.add_run()
    f = OxmlElement('w:fldSimple'); f.set(qn('w:instr'), instruction)
    r._r.addnext(f)


def init_doc():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = DInches(8.27); sec.page_height = DInches(11.69)
    sec.top_margin = DInches(.8); sec.bottom_margin = DInches(.75)
    sec.left_margin = DInches(1.0); sec.right_margin = DInches(.7)
    for name in ['Normal', 'Body Text', 'Caption', 'List Bullet']:
        st = doc.styles[name]; st.font.name = 'Times New Roman'; st.font.size = DPt(13)
        st.paragraph_format.space_after = DPt(6)
        st.paragraph_format.line_spacing = 1.15
    for name, size in [('Title', 23), ('Heading 1', 17), ('Heading 2', 14)]:
        st = doc.styles[name]; st.font.name = 'Times New Roman'; st.font.size = DPt(size)
        st.font.color.rgb = DColor.from_string(NAVY)
    sec.header.paragraphs[0].text = 'KHAI PHÁ DỮ LIỆU  |  GAMER BEHAVIOR CLUSTERING'
    sec.header.paragraphs[0].style.font.size = DPt(9)
    foot = sec.footer.paragraphs[0]; foot.alignment = 2
    foot.add_run('Trang '); field(foot, 'PAGE')
    setting = OxmlElement('w:updateFields'); setting.set(qn('w:val'), 'true')
    doc.settings.element.append(setting)
    return doc


def para(doc, text):
    p = doc.add_paragraph(text); p.paragraph_format.widow_control = True
    return p


def table(doc, caption, headers, rows, comment):
    doc.add_paragraph(caption, 'Caption')
    t = doc.add_table(rows=1, cols=len(headers)); t.style = 'Light Shading Accent 1'
    for c, h in zip(t.rows[0].cells, headers): c.text = str(h)
    repeat = OxmlElement('w:tblHeader'); t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows:
        cells = t.add_row().cells
        for c, v in zip(cells, row): c.text = str(v)
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = DPt(3)
                for r in p.runs: r.font.size = DPt(10.5)
        trpr = row._tr.get_or_add_trPr(); trpr.append(OxmlElement('w:cantSplit'))
    para(doc, comment)


def image(doc, name, caption, width=6.1):
    doc.add_picture(str(O / 'figures' / name), width=DInches(width))
    doc.add_paragraph(caption, 'Caption')


def chapter(doc, title):
    doc.add_page_break(); doc.add_heading(title, 1)


def build_report(s, p, search, ev, audit, stability):
    doc = init_doc()
    for text in ['[TÊN TRƯỜNG]', '[KHOA / VIỆN]', '', 'BÁO CÁO HỌC PHẦN KHAI PHÁ DỮ LIỆU']:
        q = doc.add_paragraph(text); q.alignment = 1
    doc.add_paragraph('GAMER BEHAVIOR CLUSTERING\n& PLAYER PROFILING', 'Title').alignment = 1
    doc.add_paragraph('Phân cụm hành vi và xây dựng hồ sơ người chơi', 'Subtitle').alignment = 1
    for text in ['Giảng viên: [Họ và tên]', 'Lớp học phần: [Mã lớp]',
                 'Thành viên 1: [Họ tên]  |  MSSV: [Mã sinh viên]',
                 'Thành viên 2: [Họ tên]  |  MSSV: [Mã sinh viên]',
                 'Ngày hoàn thiện: 22/11/2026']:
        doc.add_paragraph(text)
    para(doc, 'Bản hoàn chỉnh về nội dung và thực nghiệm. Thông tin bìa đang để chỗ điền vì chưa có mẫu trường và danh sách nhóm. Dữ liệu Kaggle là dữ liệu tổng hợp do tác giả công bố; nhóm không tạo thêm quan sát.')
    chapter(doc, 'Mục lục')
    field(doc.add_paragraph(), 'TOC \\o "1-2" \\h \\z \\u')
    para(doc, 'Nếu mục lục chưa hiển thị đúng sau khi mở: nhấn Ctrl+A, F9 và chọn cập nhật toàn bộ mục lục.')
    chapter(doc, '1. Bài toán và kết quả chính')
    best = ev[ev.method == 'Ward_KMeans'].iloc[0]
    para(doc, f'Nhóm triển khai mô hình Ward kết hợp K-Means trên {s["rows"]:,} người chơi và chọn k = {s["final_k"]}. Trên {s["n_holdout"]:,} quan sát giữ lại, Silhouette đạt {best.silhouette:.4f}, Davies–Bouldin đạt {best.davies_bouldin:.4f}. Các phân khúc cần được xem như cách chia tương đối trong dữ liệu tổng hợp, chưa phải bằng chứng về những nhóm người chơi tự nhiên ngoài thực tế.')
    para(doc, 'Mục tiêu là rút trích đặc trưng phong cách chơi, kết hợp phân cụm phân cấp với K-Means, đánh giá chất lượng và đề xuất cách tiếp cận sản phẩm theo từng nhóm. Đây là học không giám sát: không có nhãn phân khúc chuẩn để tính Accuracy, Precision hoặc ROC-AUC.')
    table(doc, 'Bảng 1. Đối chiếu yêu cầu đề bài và sản phẩm thực hiện', ['Yêu cầu', 'Cách đáp ứng / giới hạn'], [
        ['Playtime', 'Dùng PlayTimeHours, SessionsPerWeek, AvgSessionDurationMinutes; kiểm tra mâu thuẫn đơn vị.'],
        ['Win/loss ratio', 'Không có Wins/Losses; chưa tính được. Không suy ra từ EngagementLevel.'],
        ['Item collection rate', 'Không có số vật phẩm và thời gian theo dõi; AchievementsUnlocked chỉ là số thành tích tích lũy.'],
        ['Skill score', 'Không có MMR/Elo hay điểm kỹ năng; PlayerLevel chỉ phản ánh tiến trình.'],
        ['Agglomerative + K-Means', 'Ward trên mẫu train → tâm Ward → K-Means trên toàn bộ train.'],
        ['Silhouette / DBI', 'Quét k = 2…8 trên train; chấm holdout sau khi khóa k.'],
        ['Casual, Hardcore, High-Spenders', 'Đặt tên theo hồ sơ thật. Không gán High-Spenders vì thiếu số tiền.'],
        ['Monetization', 'Đề xuất theo tần suất/thời lượng; cần A/B test trước triển khai.']
    ], 'Bảng cho thấy các yêu cầu thuật toán đã được triển khai. Ba loại chỉ số hành vi và nhãn High-Spenders bị giới hạn bởi dữ liệu nguồn; báo cáo không coi các biến thay thế là phép đo tương đương.')
    chapter(doc, '2. Nguồn dữ liệu và khám phá ban đầu')
    para(doc, f'Dữ liệu gồm {audit["rows"]:,} dòng, {audit["columns"]} cột, tải trực tiếp từ Kaggle, phiên bản 1, tác giả Rabie El Kharoua, giấy phép CC BY 4.0. Data card ghi rõ bộ dữ liệu được tổng hợp phục vụ giáo dục. Link Google trong đề không phải đường tải trực tiếp; dự án sử dụng trang Kaggle nêu trong tài liệu tham khảo. Không có chứng cứ cho phép gọi đây là nhật ký người chơi thực tế.')
    rows = [
        ['PlayerID', 'Mã người chơi', 'Khóa truy vết, loại khỏi mô hình'],
        ['Age, Gender, Location', 'Thông tin nhân khẩu', 'Chỉ lưu trong dữ liệu; không dùng để phân cụm'],
        ['GameGenre, GameDifficulty', 'Thể loại, độ khó', 'Biến ngữ cảnh; không ép mã số vào khoảng cách'],
        ['PlayTimeHours', 'Nguồn mô tả giờ trung bình/phiên', 'Dùng như chỉ báo thời lượng thô; phân tích độ nhạy'],
        ['SessionsPerWeek', 'Số phiên mỗi tuần', 'Đặc trưng tần suất'],
        ['AvgSessionDurationMinutes', 'Phút trung bình mỗi phiên', 'Đặc trưng thời lượng'],
        ['PlayerLevel', 'Cấp độ hiện tại', 'Đặc trưng tiến trình, không phải kỹ năng'],
        ['AchievementsUnlocked', 'Số thành tích đã mở', 'Đặc trưng tích lũy, không phải tốc độ thu vật phẩm'],
        ['InGamePurchases', '0: không mua; 1: có mua', 'Chỉ phân tích sau phân cụm'],
        ['EngagementLevel', 'High / Medium / Low', 'Chỉ đối chiếu sau học; không làm nhãn huấn luyện']]
    table(doc, 'Bảng 2. Từ điển dữ liệu và vai trò', ['Cột', 'Ý nghĩa', 'Vai trò'], rows,
          'Mô hình học trên năm biến số. Bỏ ID và nhãn có sẵn giúp cụm phản ánh cấu trúc khoảng cách thay vì lặp lại một cách gắn nhãn trước đó. Không có biến phân loại trong đầu vào nên không cần One-Hot.')
    para(doc, f'Kiểm tra chất lượng cho thấy {audit["raw_missing_cells"]} ô thiếu ban đầu, {audit["duplicate_rows"]} dòng trùng và {audit["duplicate_player_ids"]} PlayerID lặp. Sau ép kiểu và chuyển số âm/vô cực thành thiếu, số ô thiếu của năm đặc trưng là {sum(audit["feature_missing_after_coercion"].values())}. Mỗi quan sát tương ứng một ID.')
    image(doc, '01_distributions.png', 'Hình 1. Phân phối năm đặc trưng. Trục ngang là giá trị gốc; trục dọc là số người chơi. Không suy ra có cụm tự nhiên chỉ từ histogram.')
    para(doc, f'Nếu hai cột thời lượng đo cùng một đại lượng, PlayTimeHours phải gần AvgSessionDurationMinutes / 60. Thực tế, {audit["session_time_disagreement_rate"]:.2%} quan sát lệch quá 0,1 giờ; hệ số tương quan hai cột là {audit["session_time_pearson"]:.4f}. Vì vậy không nhân PlayTimeHours với SessionsPerWeek để tạo số giờ/tuần chắc chắn. Muốn diễn giải vận hành cần hỏi lại người cung cấp dữ liệu.')
    chapter(doc, '3. Tiền xử lý và lựa chọn đặc trưng')
    para(doc, f'Dự án giữ năm đặc trưng có sẵn để mô tả tần suất, thời lượng và tiến trình; toàn bộ được chuẩn hóa. Tập train có {s["n_train"]:,} người, holdout có {s["n_holdout"]:,} người; seed = 42. Không dùng EngagementLevel để phân tầng hay lựa chọn biến.')
    para(doc, 'Đầu tiên, mã đọc CSV và xác nhận các cột bắt buộc. Khoảng trắng hoặc chuỗi không chuyển thành số được coi là thiếu bằng to_numeric(errors="coerce"). Giá trị âm và vô cực được chuyển thành thiếu theo quy tắc xác định. Kiểm tra ID trùng xảy ra trước chia mẫu; nếu phát hiện, chương trình dừng để yêu cầu quyết định thay vì xóa tùy tiện.')
    para(doc, 'Sau khi chia train/holdout, Pipeline gồm SimpleImputer(strategy="median") và StandardScaler chỉ được fit trên train. Bộ điền trung vị vẫn được lưu dù dữ liệu hiện tại không thiếu, nhằm có cách xử lý nhất quán cho đầu vào mới. Không cắt ngoại lệ chỉ vì giá trị lớn; không có bằng chứng nghiệp vụ để coi mọi người chơi lâu là lỗi.')
    para(doc, 'Công thức chuẩn hóa: zᵢⱼ = (xᵢⱼ − μⱼ,train) / σⱼ,train. Khi chưa chuẩn hóa, khoảng cách Euclidean có thể bị cột có thang đo lớn chi phối. StandardScaler dùng độ lệch chuẩn với ddof = 0. Người chơi holdout và người chơi mới dùng đúng μ, σ của train.')
    image(doc, '02_correlations.png', 'Hình 2. Tương quan Pearson của năm biến số trên toàn bộ dữ liệu, dùng cho EDA mô tả. Việc chọn mô hình không sử dụng thống kê holdout; kiểm tra độ nhạy được báo cáo riêng.')
    para(doc, 'Lựa chọn biến theo ý nghĩa dữ liệu được kết hợp với kiểm tra phương sai và tương quan. Các bảng feature_audit.csv và feature_correlations.csv lưu bằng chứng. Không dùng Mutual Information với EngagementLevel, Chi-square hay Random Forest importance vì chúng sẽ biến bước chọn biến thành có giám sát. Không thêm đồng thời số phiên × số phút/phiên vào khoảng cách vì sẽ đếm lặp hai thành phần đã có.')
    para(doc, 'PlayerLevel và AchievementsUnlocked không đo kỹ năng một cách độc lập với thời gian chơi hay luật game. Hai biến chỉ thể hiện tiến trình và tích lũy; mọi kết luận “giỏi hơn” cần điểm kỹ năng và lịch sử thi đấu. Win/loss ratio cần Wins và Losses cùng cửa sổ thời gian; khi Losses = 0 phải quy định cách làm trơn hoặc báo riêng. Item collection rate cần số vật phẩm thu được chia cho thời lượng theo dõi, không thể dùng thành tích tích lũy chia cho thời lượng trung bình một phiên.')
    chapter(doc, '4. Ba phương pháp và cơ chế kết hợp')
    para(doc, f'Ba phương pháp được so sánh trên cùng mẫu {s["n_ward_sample"]:,} quan sát lấy từ train, cùng đặc trưng đã chuẩn hóa và cùng các k = 2…8. Sau chọn k, K-Means và Ward + K-Means được fit trên toàn bộ train. Ward thuần dùng đại diện tâm để gán quan sát ngoài mẫu và được ghi rõ là mở rộng bằng tâm.')
    doc.add_heading('4.1. K-Means làm mốc so sánh', 2)
    para(doc, 'K-Means tìm k tâm sao cho tổng bình phương khoảng cách trong cụm nhỏ: J = Σᵣ Σₓ∈Cᵣ ||x − μᵣ||². Thuật toán khởi tạo tâm bằng k-means++, gán mỗi điểm cho tâm gần nhất, tính lại tâm bằng trung bình và lặp đến hội tụ. Đây là mốc đơn giản, có predict và mở rộng tốt khi số người chơi lớn.')
    para(doc, 'Dự án dùng n_init = 20, max_iter = 300, random_state = 42. Chạy nhiều khởi tạo làm giảm phụ thuộc vào một lần chọn tâm. K-Means phù hợp hơn với cụm gần dạng cầu trong khoảng cách Euclidean; nhạy với thang đo, ngoại lệ và số cụm được chỉ định. K-Means luôn chia dữ liệu thành cụm dù dữ liệu không có cấu trúc nhóm rõ.')
    para(doc, 'Mã tương ứng: KMeans(n_clusters=k, init="k-means++", n_init=20, max_iter=300, random_state=42).fit(X_train_scaled). Phần fit_models tạo kết quả chọn k; phần run fit lại trên toàn train sau khi khóa k.')
    doc.add_heading('4.2. Agglomerative Hierarchical Clustering với Ward', 2)
    para(doc, 'Ban đầu mỗi quan sát là một cụm. Ở mỗi bước, Ward gộp cặp cụm làm tăng tổng bình phương sai số ít nhất. Với hai cụm A, B: Δ(A,B) = |A||B| / (|A|+|B|) × ||μA−μB||². Dùng khoảng cách Euclidean, xây cây phân cấp rồi cắt cây để thu được k cụm.')
    para(doc, 'Mã dùng scipy.cluster.hierarchy.linkage(method="ward") và cut_tree. Đây là Agglomerative Ward thực sự, không phải chỉ vẽ cây trên tâm K-Means. Cây liên kết lưu tại ward_linkage.npy và ID mẫu tại ward_sample_ids.csv. Ward cho phép nhìn cấu trúc gộp nhiều mức nhưng không có predict tự nhiên; chi phí bộ nhớ của cách triển khai này tăng theo bình phương số quan sát.')
    image(doc, '03_dendrogram.png', 'Hình 3. Cây Ward rút gọn còn 24 nhánh cuối; ngoặc thể hiện số phần tử của nhánh. Không đọc biểu đồ như 24 người chơi riêng lẻ. k được chọn bằng chỉ số nội bộ, không chỉ bằng mắt.')
    para(doc, f'Để tránh Ward trên {s["n_train"]:,} người tạo chi phí bộ nhớ quá lớn, cây được fit trên mẫu {s["n_ward_sample"]:,} người của train. Với Ward thuần, tâm từng cụm trên mẫu được dùng để gán holdout bằng tâm gần nhất. Kết quả này phản ánh chất lượng cơ chế gán qua tâm; không được gọi là Ward chính xác trên toàn holdout hay toàn bộ dân số.')
    doc.add_heading('4.3. Ward khởi tạo, K-Means tinh chỉnh', 2)
    para(doc, 'Sau khi cắt cây Ward ở k, lấy trung bình từng cụm làm tâm khởi tạo K-Means. Trên mẫu chọn k, K-Means tinh chỉnh chính mẫu đó. Khi khóa k, tâm Ward từ mẫu train được dùng để chạy K-Means trên toàn train. Như vậy cấu trúc phân cấp tham gia trực tiếp vào quá trình huấn luyện, còn K-Means đưa toàn bộ người chơi train vào bước tối ưu.')
    para(doc, 'Mã tương ứng: ward_labels = cut_tree(tree, n_clusters=k).ravel(); init = centers_from_labels(X_sample, ward_labels); KMeans(n_clusters=k, init=init, n_init=1, max_iter=300, random_state=42).fit(X_train_scaled). n_init = 1 vì tâm khởi tạo đã được chỉ định. Mô hình cuối được lưu cùng Pipeline để tái sử dụng.')
    para(doc, 'Ưu điểm là có khởi tạo có cấu trúc và vẫn gán người chơi mới bằng K-Means. Nhược điểm là phụ thuộc mẫu Ward, chi phí xây cây và các giả định khoảng cách của K-Means. Kết hợp hai thuật toán không bảo đảm cải thiện Silhouette hay DBI; phải đọc bảng so sánh thực nghiệm.')
    chapter(doc, '5. Chọn số cụm và đánh giá chất lượng')
    para(doc, f'Số cụm được chọn riêng cho từng phương pháp từ train: {s["selected_k"]}. Phương pháp Ward + K-Means được xác định trước là sản phẩm chính theo đề. Holdout chỉ dùng để đánh giá sau khi khóa k; không dùng để chọn phương pháp thắng cuộc.')
    doc.add_heading('5.1. Hai chỉ số trả lời điều gì?', 2)
    para(doc, 'Silhouette trả lời: một người chơi có gần nhóm mình hơn nhóm lân cận không? Với a(i) là khoảng cách trung bình từ i đến các điểm khác cùng cụm; b(i) là khoảng cách trung bình nhỏ nhất tới một cụm khác: s(i) = [b(i) − a(i)] / max[a(i), b(i)]. Giá trị nằm trong [−1, 1]; gần 1 thể hiện tách tốt, gần 0 thể hiện ranh giới chồng lấn, âm thể hiện điểm gần nhóm khác hơn. Điểm toàn bộ là trung bình s(i).')
    para(doc, 'Ví dụ nhỏ để hiểu công thức: nếu a = 2, b = 5 thì s = (5−2)/5 = 0,6. Nếu a = 5, b = 2 thì s = −0,6. Ví dụ này chỉ giải thích phép tính, không được đưa vào dữ liệu thực nghiệm.')
    para(doc, f'Silhouette được tính trên một mẫu cố định {s["n_silhouette_train"]:,} người trong mẫu train và {s["n_silhouette_holdout"]:,} người trong holdout để giảm chi phí khoảng cách. Cùng một mẫu đánh giá được dùng cho tất cả phương pháp ở cùng giai đoạn. Đây là Silhouette của phân hoạch trên mẫu đánh giá; không phải phép tính đầy đủ trên {s["rows"]:,} người.')
    para(doc, 'Davies–Bouldin trả lời: độ phân tán của cụm lớn đến đâu so với khoảng cách giữa các tâm? Gọi Sᵣ là khoảng cách Euclidean trung bình đến tâm cụm r; Mᵣₛ là khoảng cách hai tâm. DBI = (1/k) Σᵣ maxₛ≠ᵣ [(Sᵣ+Sₛ)/Mᵣₛ]. DBI thấp hơn tốt hơn; không có ngưỡng phổ quát chứng minh cụm “đúng”. DBI dùng toàn bộ quan sát của từng tập đang đánh giá.')
    para(doc, 'Ví dụ: hai cụm có S₁ = S₂ = 1 và hai tâm cách nhau 4 thì tỷ số là (1+1)/4 = 0,5. Hai chỉ số đều ưu tiên cụm gọn và tách rõ trong không gian đã chuẩn hóa; chúng không đo giá trị kinh doanh hay khả năng tăng doanh thu.')
    doc.add_heading('5.2. Quy tắc chọn k và kết quả train', 2)
    para(doc, 'Trong từng phương pháp, xếp hạng Silhouette giảm dần và DBI tăng dần; chọn k có tổng hạng thấp nhất. Khi hòa, ưu tiên Silhouette cao hơn rồi k nhỏ hơn. Mỗi k đều được lưu trong model_selection.csv; không cố định k = 3 chỉ để ép tên Casual, Hardcore và High-Spenders. k = 8 là biên trên của dải đã thử, nên chỉ được xem là lựa chọn trong dải 2–8, chưa phải số cụm tối ưu toàn cục. Cần mở rộng dải và kiểm tra độ ổn định nếu muốn chốt số phân khúc vận hành.')
    table(doc, 'Bảng 3. Kết quả chọn số cụm trên cùng mẫu train', ['Phương pháp', 'k', 'Silhouette ↑', 'DBI ↓', 'Cụm nhỏ nhất (%)'],
          [[r.method, r.k, f'{r.silhouette:.4f}', f'{r.davies_bouldin:.4f}', f'{r.min_cluster_pct:.2f}'] for r in search.itertuples()],
          'So sánh hợp lệ vì cùng mẫu người chơi, đặc trưng, thang đo và mẫu Silhouette. Tổng hạng dùng đồng thời hai tiêu chí; k tốt nhất theo tổng hạng có thể khác k có Silhouette cao nhất riêng lẻ.')
    image(doc, '04_model_selection.png', 'Hình 4. Đường chỉ số theo k. Đọc Silhouette theo hướng tăng và DBI theo hướng giảm. Biểu đồ phản ánh chất lượng phân hoạch trên mẫu train, chưa chứng minh hiệu quả tiếp thị.')
    doc.add_heading('5.3. Đánh giá trên holdout và độ ổn định', 2)
    table(doc, 'Bảng 4. Kết quả trên holdout sau khi khóa k', ['Phương pháp', 'k', 'Silhouette ↑', 'DBI ↓'],
          [[r.method, r.k, f'{r.silhouette:.4f}', f'{r.davies_bouldin:.4f}'] for r in ev.itertuples()],
          f'Ward + K-Means đạt Silhouette {best.silhouette:.4f} và DBI {best.davies_bouldin:.4f}. Ward dùng gán tâm gần nhất; hai phương pháp K-Means dùng predict từ mô hình đã fit toàn train. Không kết luận phương pháp kết hợp tốt hơn nếu bảng không cho thấy điều đó.')
    para(doc, f'Thay đổi seed lấy mẫu Ward ở 7, 21, 84, 123 và 2026, giữ nguyên train/holdout và k, cho ARI trung bình so với seed 42 là {s["stability_ari_mean"]:.4f}, thấp nhất {s["stability_ari_min"]:.4f}. ARI so sánh hai cách gán nhãn có điều chỉnh ngẫu nhiên; 1 nghĩa là trùng hoàn toàn bất kể số hiệu cụm. Đây là kiểm tra độ nhạy mẫu khởi tạo, không phải ARI so với sự thật hoặc khoảng tin cậy dân số.')
    table(doc, 'Bảng 5. Độ nhạy khi đổi mẫu Ward', ['Seed', 'ARI với seed 42', 'Silhouette', 'DBI'],
          [[int(r.seed), f'{r.ari_vs_seed42:.4f}', f'{r.silhouette:.4f}', f'{r.davies_bouldin:.4f}'] for r in stability.itertuples()],
          'ARI thấp thể hiện ranh giới phân khúc phụ thuộc khởi tạo. Cần theo dõi tính ổn định trước khi dùng nhãn cụm làm điều kiện vận hành cố định.')
    para(doc, 'Kết quả Silhouette khoảng 0,15 và ARI trung bình khoảng 0,31 cho thấy các nhóm còn chồng lấn, phân hoạch nhạy với mẫu khởi tạo. Chênh lệch chỉ số giữa K-Means và mô hình kết hợp khá nhỏ và chưa có đánh giá bất định để khẳng định ưu thế chắc chắn. Dữ liệu tổng hợp có thể được chia theo hình học ngay cả khi không tồn tại kiểu người chơi tự nhiên; vì vậy không diễn giải tám cụm như tám chân dung đã được xác nhận.')
    sens = s['feature_sensitivity']
    para(doc, f'Khi bỏ PlayTimeHours nhưng giữ k = {s["final_k"]}, ARI với mô hình chính là {sens["ari_vs_main"]:.4f}; Silhouette = {sens["silhouette"]:.4f}, DBI = {sens["davies_bouldin"]:.4f}. Các chỉ số nội bộ được tính trong không gian bốn chiều khác mô hình chính nên không dùng để tuyên bố thắng thua trực tiếp. ARI cho biết việc bỏ cột mâu thuẫn ngữ nghĩa làm thay đổi gán nhóm đến đâu. Cần xác minh đơn vị trước khi triển khai.')
    image(doc, '08_silhouette.png', 'Hình 5. Silhouette theo cụm trên mẫu 2.000 quan sát từ toàn bộ dữ liệu, chỉ dùng để mô tả bổ sung. Đường đứt là trung bình trên mẫu này, có thể khác điểm holdout của Bảng 4.')
    chapter(doc, '6. Hồ sơ người chơi và diễn giải cụm')
    para(doc, f'Mô hình cuối fit trên train và gán toàn bộ {s["rows"]:,} người để xây hồ sơ. Vì bảng hồ sơ trộn train và holdout cho mục đích mô tả, không dùng các trung bình này làm thước đo chất lượng ngoài mẫu. Mã số cụm chỉ là định danh, không phải thứ hạng.')
    table(doc, 'Bảng 6. Quy mô và đặc trưng trung bình của các cụm', ['Cụm', 'Số người', '%', 'Phiên/tuần', 'Phút/phiên', 'Cấp độ', 'Thành tích', '% mua'],
          [[int(r.cluster), f'{r.count:,}', f'{r.share_pct:.2f}', f'{r.SessionsPerWeek:.2f}', f'{r.AvgSessionDurationMinutes:.2f}', f'{r.PlayerLevel:.2f}', f'{r.AchievementsUnlocked:.2f}', f'{r.purchase_rate*100:.2f}'] for r in p.itertuples()],
          'Mỗi hàng biểu diễn trung bình và quy mô thật của một cụm. “% mua” chỉ là tỷ lệ InGamePurchases = 1; không phản ánh doanh thu, tần suất mua hoặc mức chi tiêu cao.')
    for r in p.itertuples():
        para(doc, f'Cụm {r.cluster}: {r.profile}. Nhóm có {r.count:,} người ({r.share_pct:.2f}%), trung bình {r.SessionsPerWeek:.2f} phiên/tuần và {r.AvgSessionDurationMinutes:.2f} phút/phiên. PlayTimeHours trung bình {r.PlayTimeHours:.2f} theo thang gốc chưa xác minh; cấp độ {r.PlayerLevel:.2f}, thành tích {r.AchievementsUnlocked:.2f}. Tỷ lệ có mua là {r.purchase_rate:.2%}. Tên hồ sơ chỉ thể hiện so sánh tương đối giữa các cụm trong chính bộ dữ liệu.')
    para(doc, 'Quy tắc đặt tên có thể kiểm tra trong profile_clusters: xếp hạng trung bình số phiên và số phút mỗi phiên giữa các cụm, chia tương đối ở nửa trên/nửa dưới. Với số cụm lẻ, tên không nhất thiết duy nhất. Không coi “chơi thường xuyên” là chẩn đoán nghiện game; không coi “phiên ngắn” là ít gắn bó trong mọi thể loại.')
    image(doc, '06_profiles.png', 'Hình 6. Màu nóng nghĩa là trung bình cụm cao hơn trung bình chung theo đơn vị độ lệch chuẩn; màu lạnh là thấp hơn. Các ô là z-score trung bình để so các thang đo khác nhau.')
    image(doc, '05_pca.png', f'Hình 7. PCA 2D biểu diễn {s["pca_2d_variance"]:.2%} phương sai. Điểm chồng lấn ở hình chiếu không tự phủ định hoặc xác nhận phân hoạch năm chiều; PCA không được dùng khi học cụm.')
    image(doc, '07_sizes_purchases.png', 'Hình 8. Quy mô cụm và tỷ lệ có mua hàng. Trục phần trăm cố định 0–100 giúp tránh phóng đại các khác biệt nhỏ.')
    chapter(doc, '7. Chiến lược sản phẩm và kiếm tiền có mục tiêu')
    para(doc, 'Đề xuất dưới đây là giả thuyết cần thử nghiệm. Dữ liệu không có doanh thu, thời điểm mua, chi phí chiến dịch hoặc biến can thiệp; vì vậy không tính được uplift, ROI hay mức tăng doanh thu từ phân cụm. Chênh lệch tỷ lệ mua giữa cụm chưa chứng minh khả năng phản ứng với ưu đãi.')
    strategy_rows = []
    for r in p.itertuples():
        short = 'phiên ngắn' in r.profile
        frequent = 'thường xuyên' in r.profile
        offer = ('Vật phẩm trang trí nhỏ, gói trải nghiệm dễ hiểu' if short else 'Gói trang trí theo chủ đề, nội dung mở rộng tự chọn')
        channel = ('Hiển thị tại thời điểm kết thúc phiên, giới hạn tần suất' if frequent else 'Thông điệp khi quay lại game; nhiệm vụ ngắn để làm quen')
        strategy_rows.append([f'{r.cluster}: {r.profile}', offer, channel, 'Conversion; doanh thu/người đủ điều kiện; D7 retention; hoàn tiền'])
    table(doc, 'Bảng 7. Giả thuyết đề xuất theo phân khúc', ['Cụm / hồ sơ', 'Nội dung thử nghiệm', 'Điểm chạm', 'Đo lường'], strategy_rows,
          'Mỗi đề xuất liên hệ với số phiên và thời lượng, chưa được xem là chiến dịch đã chứng minh hiệu quả. Không dùng nhãn High-Spenders vì thiếu số tiền và lịch sử mua.')
    para(doc, 'Thiết kế thử nghiệm: chọn người đủ điều kiện, phân ngẫu nhiên control/treatment bên trong từng cụm, giữ nguyên giá và điều kiện giữa hai nhánh nếu chỉ thử thông điệp. Khóa nhãn cụm trước thử nghiệm. Chỉ số chính là conversion hoặc doanh thu bình quân trên toàn bộ người đủ điều kiện được phân nhánh, kể cả người không mua. Theo dõi thêm retention D7/D30, tỷ lệ hoàn tiền và phản hồi tiêu cực.')
    para(doc, 'Bổ sung dữ liệu cần thiết gồm purchase_amount, currency, purchase_timestamp, số trận thắng/thua theo tuần, số vật phẩm và thời gian thu thập, điểm MMR/Elo, cửa sổ quan sát và hoạt động quay lại. Có doanh thu mới xây được RFM hoặc nhóm chi tiêu cao theo ngưỡng được thống nhất. Không đồng nhất số thành tích lớn với mức sẵn sàng chi trả.')
    para(doc, 'Vì dữ liệu có thông tin tuổi, thử nghiệm thương mại cần dùng nhóm đủ điều kiện về tuổi theo chính sách sản phẩm và có kiểm soát phù hợp. Đề xuất ưu tiên trang trí, quyền chọn rõ ràng, giới hạn nhắc mua; không tạo áp lực tăng thời gian chơi hay mua lợi thế cạnh tranh. Phân cụm chính không dùng nhân khẩu học để đặt giá.')
    chapter(doc, '8. Tái lập, hạn chế và hướng phát triển')
    para(doc, 'Mã chính chạy từ CSV đến bảng, hình, mô hình và ví dụ gán nhóm. Mô hình đóng gói gồm bộ điền thiếu, scaler, danh sách cột và K-Means. Khi gán người chơi mới, chỉ transform và predict; không fit lại trên đầu vào mới. Tên cụm có thể đổi nếu huấn luyện lại và cần ánh xạ trước so sánh các phiên bản.')
    para(doc, 'Chạy: python -m venv .venv; kích hoạt môi trường; pip install -r requirements.txt; python gamer_clustering.py. Tạo tài liệu bằng python build_deliverables.py. Dự đoán CSV mới bằng python gamer_clustering.py --predict duong_dan.csv. README mô tả từng bước riêng để dùng trên Windows hoặc Linux. Mô hình joblib chỉ nên mở từ nguồn tin cậy và cùng phiên bản thư viện.')
    table(doc, 'Bảng 8. Các tệp kiểm chứng chính', ['Tệp', 'Mục đích'], [
        ['summary.json; run.log', 'Kết quả tổng hợp, seed, kích thước mẫu, thời gian, phiên bản'],
        ['model_selection.csv', 'Toàn bộ 21 cấu hình phương pháp × k'],
        ['holdout_metrics.csv; stability.csv', 'Đánh giá ngoài mẫu và độ nhạy khởi tạo'],
        ['data_audit.json; feature_sensitivity.json', 'Kiểm tra dữ liệu và ảnh hưởng bỏ PlayTimeHours'],
        ['cluster_profiles.csv; player_assignments.csv', 'Trung bình cụm và nhãn từng người'],
        ['split.csv; ward_sample_ids.csv', 'Truy vết chia train/holdout và mẫu Ward'],
        ['player_cluster_model.joblib', 'Pipeline và mô hình để gán nhóm mới']
    ], 'Các con số trong báo cáo và slide được đọc tự động từ các tệp kết quả này; dữ liệu nguồn được nhận diện bằng SHA-256 để tránh nhầm phiên bản.')
    para(doc, f'SHA-256 của CSV: {s["data_sha256"]}. Môi trường chạy Python {s["python"]}, scikit-learn {s["versions"]["scikit-learn"]}; thời gian chạy pipeline lần ghi nhận khoảng {s["runtime_seconds"]:.1f} giây, không bao gồm cài thư viện và xuất tài liệu. Thời gian có thể thay đổi theo máy.')
    para(doc, 'Giới hạn chính: dữ liệu tổng hợp; thiếu thắng/thua, vật phẩm theo thời gian và doanh thu; hai cột thời lượng có mâu thuẫn; Ward dùng mẫu; Silhouette dùng mẫu con; quy tắc khoảng cách Euclidean thiên về cụm gọn; kiểm tra seed chỉ là một dạng độ nhạy. Tách holdout ngẫu nhiên kiểm tra khả năng gán cùng phân phối, chưa kiểm tra hành vi tương lai hoặc game khác.')
    para(doc, 'Hướng phát triển gồm xác minh đơn vị, thống nhất cửa sổ quan sát, thu thập dữ liệu log thật, kiểm tra trên một giai đoạn tương lai, thử thuật toán mật độ khi có lý do nghiệp vụ, và thực hiện A/B test có đối chứng. Không áp dụng SMOTE hoặc stratify theo nhãn phân loại vì đây là bài toán phân cụm.')
    chapter(doc, '9. Kết luận và tài liệu tham khảo')
    para(doc, f'Nhóm đã thực hiện quy trình phân cụm hành vi với năm đặc trưng, ba phương pháp và hai chỉ số theo đề. Ward + K-Means chọn {s["final_k"]} cụm, đạt Silhouette {best.silhouette:.4f}, DBI {best.davies_bouldin:.4f} trên holdout. Kết quả cho phép mô tả khác biệt tương đối về tần suất, thời lượng và tiến trình, đồng thời cho thấy cần kiểm tra độ ổn định và ý nghĩa nguồn trước khi dùng trong vận hành.')
    para(doc, 'Sản phẩm chính là pipeline có thể chạy lại, hồ sơ từng nhóm và các giả thuyết chiến lược có thể kiểm chứng. Đề xuất kiếm tiền cần dữ liệu giao dịch và thử nghiệm có đối chứng; chưa có cơ sở để khẳng định nhóm chi tiêu cao hoặc mức tăng doanh thu.')
    refs = [
        f'[1] Rabie El Kharoua. Predict Online Gaming Behavior Dataset, phiên bản 1, 2024. Kaggle. CC BY 4.0. {SOURCE} (truy cập 22/11/2026). Bản metadata và data card được lưu trong data/.',
        f'[2] Scikit-learn. Clustering: K-Means, hierarchical clustering, silhouette và Davies–Bouldin. {DOCS} (truy cập 22/11/2026).',
        '[3] SciPy. scipy.cluster.hierarchy.linkage và cut_tree. https://docs.scipy.org/doc/scipy/reference/cluster.hierarchy.html',
        '[4] Creative Commons. Attribution 4.0 International. https://creativecommons.org/licenses/by/4.0/']
    for t in refs: para(doc, t)
    doc.save(D / 'Bao_cao_Gamer_Clustering.docx')


def presentation_content(s, p, ev):
    b = ev[ev.method == 'Ward_KMeans'].iloc[0]
    sens = s['feature_sensitivity']
    profile_lines = [f'{s["final_k"]} cụm; mỗi cụm chiếm {p.share_pct.min():.1f}–{p.share_pct.max():.1f}%',
                     'Tên tương đối: tần suất chơi × thời lượng phiên',
                     f'Tỷ lệ có mua: {p.purchase_rate.min():.1%}–{p.purchase_rate.max():.1%}']
    content = [
      ('Phân cụm hành vi người chơi', ['Gamer Behavior Clustering & Player Profiling', 'Ward + K-Means | Học phần Khai phá dữ liệu', '[Thành viên 1 – MSSV]  •  [Thành viên 2 – MSSV]'], None,
       'Em chào thầy và các bạn. Nhóm em trình bày đề tài phân cụm hành vi và xây dựng hồ sơ người chơi. Mục tiêu là tìm các nhóm có cách chơi gần nhau, sau đó đề xuất cách giới thiệu nội dung phù hợp. Nhóm sử dụng phân cụm phân cấp Ward để khởi tạo tâm cho K-Means. Bài trình bày đi từ dữ liệu, cách chọn đặc trưng, cơ chế kết hợp đến kết quả và đề xuất. Có một giới hạn em xin nói ngay: dữ liệu trên Kaggle được tác giả công bố là tổng hợp phục vụ học tập. Các kết luận kinh doanh vì vậy được trình bày dưới dạng giả thuyết.'),
      ('Bốn câu hỏi dẫn dắt dự án', ['Dữ liệu đo được những hành vi nào?', 'Ward kết hợp K-Means như thế nào?', 'Các cụm có gọn, tách biệt và ổn định?', 'Có thể thử chiến lược nào cho từng nhóm?'], None,
       'Nhóm chia đề thành bốn câu hỏi. Thứ nhất là dữ liệu thực sự đo được gì, vì tên biến có thể khiến mình suy diễn quá mức. Thứ hai là hai thuật toán phải kết hợp trong mã như thế nào, chứ không chỉ chạy riêng rồi đặt cạnh nhau. Thứ ba là cách đánh giá khi không có nhãn phân khúc chuẩn. Câu hỏi cuối cùng là chuyển kết quả thành đề xuất sản phẩm. Với mỗi câu hỏi, nhóm đều có tệp kiểm chứng tương ứng trong thư mục outputs. Các số trên slide được lấy từ kết quả chạy, không nhập số minh họa vào phần thực nghiệm.'),
      (f'{s["rows"]:,} người chơi, 13 cột từ Kaggle', ['Tác giả: Rabie El Kharoua | phiên bản 1 | CC BY 4.0', 'Nguồn tự xác nhận: dữ liệu tổng hợp cho giáo dục', 'Một hàng là một PlayerID; chưa có nhật ký giao dịch'], None,
       f'Bộ dữ liệu có {s["rows"]:,} dòng và 13 cột. Mỗi hàng là một mã người chơi, kèm tần suất chơi, thời lượng, cấp độ, thành tích và một số thông tin ngữ cảnh. Nhóm tải trực tiếp CSV từ Kaggle và lưu cả metadata để kiểm tra tác giả, phiên bản, giấy phép. Data card ghi rõ đây là dữ liệu tổng hợp. Vì thế, nhóm có thể đánh giá quy trình thuật toán trên đúng bộ được giao, nhưng chưa thể xem các cụm là phân khúc thật của một trò chơi cụ thể. Bộ dữ liệu cũng không có thời điểm bắt đầu và kết thúc theo dõi từng người.'),
      ('Ba chỉ số đề bài chưa có dữ liệu để tính', ['Không có Wins/Losses → chưa có tỷ lệ thắng/thua', 'Thành tích tích lũy ≠ tốc độ thu vật phẩm', 'Cấp độ ≠ điểm kỹ năng; có mua ≠ chi tiêu cao', 'Hai cột thời lượng chưa thống nhất đơn vị'], None,
       'Đề bài gợi ý tỷ lệ thắng thua, tốc độ thu vật phẩm và điểm kỹ năng. Tuy nhiên, nguồn không có số trận thắng hoặc thua, không có vật phẩm thu được theo thời gian, cũng không có MMR hay Elo. Nhóm không tự tạo các cột này. PlayerLevel được dùng như chỉ báo tiến trình, còn AchievementsUnlocked là số thành tích tích lũy. InGamePurchases chỉ cho biết có mua hay không, nên không đặt tên High-Spenders. Hai cột thời lượng cũng không khớp khi đổi phút sang giờ. Nhóm giữ cột gốc cho thực nghiệm và có kiểm tra khi loại PlayTimeHours để minh bạch ảnh hưởng.'),
      ('Năm biến mô tả tần suất, thời lượng, tiến trình', ['PlayTimeHours; SessionsPerWeek', 'AvgSessionDurationMinutes', 'PlayerLevel; AchievementsUnlocked', 'Loại ID; giữ EngagementLevel và mua hàng để đối chiếu sau'], '01_distributions.png',
       'Năm đầu vào gồm thời lượng thô PlayTimeHours, số phiên mỗi tuần, số phút trung bình mỗi phiên, cấp độ và số thành tích. Biểu đồ cho thấy phân phối từng biến trước chuẩn hóa. Nhóm chọn chúng vì liên quan trực tiếp đến phong cách chơi và đều là số. PlayerID bị loại vì số mã lớn hơn không có nghĩa là hành vi mạnh hơn. EngagementLevel được giữ lại để đối chiếu sau học, tránh làm mô hình lặp lại nhãn có sẵn. Thông tin mua hàng cũng không đưa vào khoảng cách, nhờ vậy tỷ lệ mua sau phân cụm không bị quyết định sẵn bởi đầu vào.'),
      ('Chuẩn hóa chỉ học từ tập train', [f'Train: {s["n_train"]:,} | Holdout: {s["n_holdout"]:,} | seed 42', 'Ép kiểu → kiểm tra → imputer trung vị → StandardScaler', 'Fit imputer/scaler trên train; holdout chỉ transform', 'Không xóa ngoại lệ chỉ vì người chơi hoạt động nhiều'], None,
       f'Nhóm chia ngẫu nhiên dữ liệu theo tỷ lệ 80–20. Có {s["n_train"]:,} người trong train và {s["n_holdout"]:,} người trong holdout. Bộ điền thiếu và chuẩn hóa chỉ học từ train. Khi đánh giá hoặc gán người chơi mới, nhóm dùng lại các tham số đó. Chuẩn hóa giúp số phút, số phiên và cấp độ đóng góp trên thang đo tương đương trong khoảng cách Euclidean. Bước kiểm tra hiện không phát hiện ô thiếu hoặc ID lặp trong bản nguồn. Nhóm vẫn lưu imputer trong Pipeline để đầu vào mới được xử lý thống nhất. Việc chuẩn hóa và chọn k không sử dụng nhãn EngagementLevel.'),
      ('Tương quan giúp kiểm tra, không tạo nhãn học', ['Kiểm tra phương sai và tương quan', 'Không chọn biến bằng EngagementLevel', 'Không thêm chỉ số dẫn xuất đếm lặp số phiên × số phút', 'PlayTimeHours cần xác minh ý nghĩa trước triển khai'], '02_correlations.png',
       'Hình này biểu diễn tương quan tuyến tính giữa các đầu vào. Nó giúp kiểm tra cột quá giống nhau và là một phần của khám phá dữ liệu, chứ không phải nhãn đúng sai cho cụm. Nhóm không dùng Random Forest hay Mutual Information với EngagementLevel để chọn đầu vào vì đó sẽ đưa thông tin có giám sát vào thiết kế phân cụm. Việc chọn năm biến dựa trên mục tiêu và khả năng đo được của nguồn. Các thống kê kiểm tra được lưu trong feature_audit và feature_correlations. Đến đây em xin chuyển phần thuật toán và đánh giá cho bạn thứ hai trong nhóm.'),
      ('K-Means là mốc so sánh dễ tái lập', ['Gán điểm cho tâm gần nhất → tính lại trung bình', 'Mục tiêu: giảm tổng bình phương khoảng cách trong cụm', 'k-means++ | 20 khởi tạo | tối đa 300 vòng', 'Nhanh; cần chọn k và nhạy với hình dạng cụm'], None,
       'Em xin tiếp tục phần mô hình. K-Means bắt đầu bằng k tâm, rồi lặp hai bước: gán người chơi cho tâm gần nhất và tính lại tâm bằng trung bình những người trong nhóm. Mục tiêu là giảm tổng bình phương khoảng cách đến tâm. Nhóm dùng k-means++ và chạy 20 lần khởi tạo cho mỗi k để giảm phụ thuộc một lần chọn tâm. Đây là mốc so sánh vì đơn giản, dễ lưu và có thể predict cho người chơi mới. Tuy nhiên, K-Means luôn tạo nhóm ngay cả khi dữ liệu gần liên tục. Nó cũng thích các nhóm gọn nên chỉ số tốt cần được đọc cùng hồ sơ và độ ổn định.'),
      ('Ward gộp cụm theo mức tăng sai số nhỏ nhất', [f'Xây cây trên {s["n_ward_sample"]:,} người lấy từ train', 'Mỗi bước gộp làm tăng phương sai nội cụm ít nhất', 'Cắt cây ở k = 2…8; lưu cây và ID mẫu', 'Ward ngoài mẫu: gán qua tâm, cần ghi rõ'], '03_dendrogram.png',
       f'Ward là phân cụm phân cấp kết tụ. Ban đầu mỗi người là một cụm; thuật toán lần lượt gộp hai cụm khiến tổng sai số tăng ít nhất. Cây trên slide được rút gọn còn 24 nhánh cuối, các số trong ngoặc là số quan sát của nhánh. Nhóm xây cây trên {s["n_ward_sample"]:,} người lấy từ train để kiểm soát bộ nhớ. Ward thuần không có predict tự nhiên. Vì vậy khi đánh giá trên holdout, nhóm dùng tâm của các cụm Ward để gán điểm gần nhất và ghi rõ đây là mở rộng bằng tâm, không gọi là chạy Ward trực tiếp trên toàn bộ người chơi.'),
      ('Tâm Ward được K-Means tinh chỉnh trên toàn train', ['Ward trên mẫu train → cắt cây ở k', 'Lấy trung bình mỗi cụm → tâm khởi tạo', 'K-Means fit toàn train với n_init = 1', 'Lưu Pipeline + mô hình; người mới chỉ transform/predict'], None,
       'Cơ chế kết hợp thực sự nằm ở tâm khởi tạo. Nhóm cắt cây Ward thành k cụm, lấy trung bình của từng cụm và đưa các tâm đó vào tham số init của K-Means. Sau khi chọn k bằng mẫu train, K-Means được chạy trên toàn train để tinh chỉnh lại tâm với nhiều dữ liệu hơn. n_init bằng một vì tâm đã được xác định từ Ward. Cách làm này tận dụng cấu trúc phân cấp và giữ được khả năng gán người mới của K-Means. Nó không bảo đảm tốt hơn khởi tạo k-means++, nên nhóm vẫn chạy mốc so sánh và trình bày đầy đủ kết quả.'),
      ('Hai chỉ số nội bộ đo độ gọn và tách biệt', ['Silhouette ↑: s = (b − a) / max(a, b)', 'a: khoảng cách nội cụm; b: đến cụm lân cận', 'Davies–Bouldin ↓: phân tán / khoảng cách hai tâm', 'Không dùng Accuracy; không có nhãn phân khúc chuẩn'], None,
       'Silhouette so sánh mức gần nhóm mình với mức gần nhóm lân cận. Nếu khoảng cách trung bình trong nhóm là hai và đến nhóm gần nhất là năm thì điểm bằng ba chia năm, tức 0,6. Gần một là tách rõ; gần không là chồng lấn; âm là gần nhóm khác hơn. Davies–Bouldin lấy độ phân tán của các nhóm so với khoảng cách giữa tâm, nên càng thấp càng tốt. Hai chỉ số đo cấu trúc hình học, chưa đo doanh thu. Nhóm không tính Accuracy vì không có nhãn phân khúc thật. Silhouette dùng mẫu cố định 2.000 người để kiểm soát chi phí, còn DBI dùng toàn bộ tập đang đánh giá.'),
      (f'Quét k = 2…8; mô hình kết hợp chọn k = {s["final_k"]}', ['Ba phương pháp dùng cùng mẫu train và đặc trưng', 'Xếp hạng Silhouette giảm + DBI tăng trong từng phương pháp', f'k được chọn: {s["selected_k"]}', 'Khóa k trước khi đánh giá holdout'], '04_model_selection.png',
       f'Nhóm thử các k từ hai đến tám trên cùng mẫu train để so sánh công bằng. Với từng phương pháp, nhóm cộng thứ hạng Silhouette theo chiều giảm và DBI theo chiều tăng; tổng hạng nhỏ nhất được chọn. Khi hòa, ưu tiên Silhouette cao hơn rồi k nhỏ hơn. Cách này tránh chọn một chỉ số tùy ý sau khi nhìn kết quả. Mô hình Ward kết hợp K-Means chọn k bằng {s["final_k"]}. Nhóm không ép thành ba cụm chỉ vì đề có ba tên ví dụ. Sau bước này, k được khóa và holdout mới được dùng để đánh giá khả năng gán trên những người chưa tham gia học tâm.'),
      (f'Holdout: Silhouette {b.silhouette:.3f}, DBI {b.davies_bouldin:.3f}', [f'{r.method}: k={r.k} | Sil={r.silhouette:.3f} | DBI={r.davies_bouldin:.3f}' for r in ev.itertuples()] + ['Ward dùng mở rộng bằng tâm; hai K-Means fit toàn train', 'Điểm nội bộ chưa xác nhận giá trị kinh doanh'], None,
       f'Trên holdout, mô hình kết hợp đạt Silhouette {b.silhouette:.4f} và Davies–Bouldin {b.davies_bouldin:.4f}. Các hàng còn lại là kết quả của hai mốc so sánh sau khi chọn k riêng từ train. Cần lưu ý Ward ở đây là gán qua tâm của mẫu, còn hai phương pháp K-Means đã tinh chỉnh trên toàn train. Nhóm không chọn lại phương pháp dựa trên holdout. Mô hình kết hợp là sản phẩm chính theo yêu cầu đề; nếu K-Means thuần có chỉ số tốt hơn ở bảng thì nhóm vẫn giữ và giải thích trung thực. Điểm Silhouette gần không cho thấy ranh giới còn chồng lấn, nên cần thận trọng khi biến nhãn nhóm thành quy tắc kinh doanh.'),
      ('Các cụm còn chồng lấn, nhạy với mẫu', [f'5 mẫu Ward khác: ARI trung bình {s["stability_ari_mean"]:.3f}', f'ARI thấp nhất: {s["stability_ari_min"]:.3f}', f'Bỏ PlayTimeHours: ARI với mô hình chính {sens["ari_vs_main"]:.3f}', 'k = 8 ở biên dải thử; chưa xác nhận 8 nhóm tự nhiên'], None,
       f'Nhóm còn thay đổi mẫu Ward qua năm seed và so cách gán trên cùng holdout. ARI trung bình so với mô hình gốc là {s["stability_ari_mean"]:.4f}; giá trị thấp nhất là {s["stability_ari_min"]:.4f}. ARI bằng một nghĩa là hai cách chia trùng nhau sau khi bỏ qua số hiệu nhãn. Đây là phép đo ổn định, không phải độ chính xác so với sự thật. Khi bỏ PlayTimeHours, ARI với mô hình chính là {sens["ari_vs_main"]:.4f}. Phép thử này cho thấy mức phụ thuộc vào cột có vấn đề ngữ nghĩa. Nhóm không so trực tiếp Silhouette của bốn chiều và năm chiều để tuyên bố phương án thắng.'),
      ('Tên nhóm bám vào hồ sơ quan sát được', profile_lines + ['Cấp độ là tiến trình; % có mua không đo mức chi tiêu'], '06_profiles.png',
       'Nhóm đặt tên dựa trên trung bình số phiên và thời lượng giữa các cụm: thường xuyên hay ít phiên, phiên dài hay ngắn theo nghĩa tương đối. Heatmap thể hiện trung bình đã đổi về đơn vị độ lệch chuẩn: ô màu nóng cao hơn trung bình chung, ô màu lạnh thấp hơn. Các tên không phải nhãn được đưa trước vào mô hình. Nhóm cũng không tự thêm High-Spenders vì nguồn chỉ có cờ có mua. Hồ sơ được mô tả trên toàn bộ dữ liệu sau khi mô hình đã fit train, nên bảng hồ sơ là mô tả tổng thể, không phải một phép đánh giá holdout khác.'),
      (f'PCA 2D chỉ giữ {s["pca_2d_variance"]:.1%} phương sai', ['Hình chiếu hỗ trợ quan sát, không dùng để học cụm', 'Màu là cụm được học trong không gian năm chiều', 'Không suy ra mức tách biệt chỉ từ hình 2D', 'Đọc cùng Silhouette và độ ổn định ARI'], '05_pca.png',
       f'Biểu đồ này giúp nhìn một phần cách các nhóm phân bố. Nhóm dùng PCA để chiếu năm đầu vào xuống hai chiều, giữ khoảng {s["pca_2d_variance"]:.1%} phương sai. Mô hình phân cụm được học trong không gian năm chiều đã chuẩn hóa; PCA chỉ được dùng sau đó để minh họa. Vì còn phần lớn thông tin ở các chiều chưa vẽ, điểm chồng lấn trên hình không đủ để kết luận mọi cụm đều sai, và các vùng màu cũng không chứng minh có các kiểu người chơi tự nhiên. Nhóm đọc hình cùng điểm Silhouette còn thấp và ARI nhạy với mẫu, từ đó giữ cách diễn giải thận trọng cho ứng dụng.'),
      ('Đề xuất ưu đãi phải được kiểm chứng bằng A/B test', ['Phiên ngắn: gói trang trí nhỏ, nội dung dễ trải nghiệm', 'Phiên dài: nội dung mở rộng và chủ đề tự chọn', 'Ít phiên: điểm chạm khi quay lại; giới hạn nhắc mua', 'Đo conversion, doanh thu/người, retention và hoàn tiền'], '07_sizes_purchases.png',
       'Từ hồ sơ, nhóm đề xuất nội dung dễ trải nghiệm và gói trang trí nhỏ cho nhóm có phiên ngắn. Với phiên dài, có thể thử nội dung mở rộng hoặc trang trí theo chủ đề. Nhóm ít phiên cần điểm chạm khi quay lại game, còn tần suất nhắc mua cần giới hạn. Đây đều là giả thuyết. Muốn kiểm chứng, cần chia ngẫu nhiên control và treatment trong từng cụm, khóa nhãn trước khi thử và đo trên tất cả người đủ điều kiện được phân nhánh. Chỉ số gồm conversion hoặc doanh thu bình quân, đi kèm retention và hoàn tiền. Không có dữ liệu số tiền nên nhóm chưa thể tính ROI hay dự báo tăng doanh thu.'),
      ('Pipeline tái lập được; kết luận cần đúng phạm vi', ['Đủ mã nguồn, dữ liệu nguồn, bảng, hình và mô hình', 'Ward → tâm → K-Means; hai chỉ số và kiểm tra độ nhạy', 'Bổ sung wins/losses, vật phẩm theo thời gian, MMR, giao dịch', 'Cảm ơn thầy và các bạn • Hỏi đáp'], None,
       'Nhóm đã hoàn thành quy trình từ dữ liệu đến phân cụm, đánh giá và diễn giải. Sản phẩm nộp có mã chạy lại, CSV nguồn, bảng kết quả, hình và mô hình đã lưu. Điểm cần nhớ là việc kết hợp Ward với K-Means được thực hiện bằng tâm khởi tạo, còn đánh giá có holdout và kiểm tra độ nhạy. Giới hạn nằm ở dữ liệu tổng hợp và các chỉ số còn thiếu. Để áp dụng thật, cần xác minh đơn vị, thu thập thắng thua, vật phẩm theo thời gian, điểm kỹ năng và giao dịch, rồi thử chiến lược có đối chứng. Phần trình bày của nhóm em kết thúc. Em cảm ơn thầy và các bạn đã lắng nghe.')
    ]
    return content


def textbox(slide, text, x,y,w,h,size=22,color=INK,bold=False):
    sh = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = sh.text_frame; tf.word_wrap = True
    tf.margin_left=Inches(.02); tf.margin_right=Inches(.02)
    for i, line in enumerate(text.split('\n')):
        pp = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        pp.text=line; pp.font.name='Arial'; pp.font.size=Pt(size)
        pp.font.bold=bold; pp.font.color.rgb=RGBColor.from_string(color)
        pp.space_after=Pt(10)
    return sh


def build_slides(content):
    from pptx.enum.shapes import MSO_SHAPE
    prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
    for i,(title,bullets,img,notes) in enumerate(content,1):
        sl=prs.slides.add_slide(prs.slide_layouts[6])
        bg=sl.background.fill; bg.solid(); bg.fore_color.rgb=RGBColor.from_string('F5F8FA')
        band=sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,prs.slide_width,Inches(.12))
        band.fill.solid(); band.fill.fore_color.rgb=RGBColor.from_string(TEAL); band.line.fill.background()
        titlebox=textbox(sl,title,.55,.42,12.2,.86,29,NAVY,True); titlebox.name='STATIC_TITLE'
        label='DỮ LIỆU' if i<8 else 'MÔ HÌNH & ĐÁNH GIÁ' if i<15 else 'HỒ SƠ & ỨNG DỤNG'
        textbox(sl,label,.58,1.28,12,.35,11,TEAL,True).name='STATIC_SECTION'
        if img:
            textbox(sl,'\n'.join('• '+b for b in bullets),.6,1.95,4.15,4.65,20,INK)
            # Fit ảnh trong khung 7.65 × 4.75 bằng kích thước thật, không kéo méo.
            from PIL import Image
            path=O/'figures'/img
            iw,ih=Image.open(path).size; ratio=iw/ih
            ww,hh=7.55,4.85
            if ww/hh>ratio: ww=hh*ratio
            else: hh=ww/ratio
            sl.shapes.add_picture(str(path),Inches(5.05+(7.55-ww)/2),Inches(1.9+(4.85-hh)/2),width=Inches(ww),height=Inches(hh))
        else:
            if i==1:
                textbox(sl,'WARD  →  TÂM CỤM  →  K-MEANS',.65,2.02,12,1,34,TEAL,True)
                textbox(sl,'\n'.join(bullets),.65,3.42,11.9,2.5,25,INK)
            else:
                for j,b in enumerate(bullets):
                    textbox(sl,f'{j+1:02}',.65,2+j*.85,.65,.6,23,TEAL,True)
                    textbox(sl,b,1.5,2+j*.85,11,.72,23,INK)
        textbox(sl,'KHAI PHÁ DỮ LIỆU  •  Kaggle: Rabie El Kharoua, CC BY 4.0',.6,7.08,11,.24,9,GRAY).name='STATIC_FOOTER'
        textbox(sl,f'{i:02} / {len(content)}',12,7.04,.8,.3,11,GRAY).name='STATIC_NUMBER'
        sl.notes_slide.notes_text_frame.text=f'Người {1 if i<=7 else 2} | khoảng 45–50 giây\n\n'+notes
        transition=PX('p:transition'); transition.set('spd','med'); transition.append(PX('p:fade'))
        sl.element.insert(list(sl.element).index(sl.element.find('{http://schemas.openxmlformats.org/presentationml/2006/main}clrMapOvr'))+1,transition)
    prs.save(D/'Thuyet_trinh_Gamer_Clustering.pptx')


def build_speech(content,s):
    doc=init_doc(); doc.add_heading('Bài nói và câu hỏi bảo vệ',0)
    para(doc, 'Thời lượng dự kiến 13–15 phút, cần diễn tập để điều chỉnh tốc độ. Người 1 trình bày slide 1–7; người 2 trình bày slide 8–18. Thay tên trước khi thuyết trình. Bản ngắn ở cuối giúp ôn nhanh; lời đầy đủ cũng có trong Notes của từng slide.')
    for i,(title,bullets,img,notes) in enumerate(content,1):
        doc.add_heading(f'Slide {i}. {title}',2)
        para(doc,f'Người {1 if i<=7 else 2} | 45–50 giây')
        para(doc,notes)
    chapter(doc,'Câu hỏi thầy có thể hỏi')
    qa=[
      ['Vì sao không dùng Accuracy?', 'Không có nhãn phân khúc chuẩn; dùng Silhouette, DBI cho cấu trúc cụm và ARI cho độ ổn định.', 'Người 2'],
      ['Ward kết hợp K-Means ở đâu trong code?', 'Cắt cây Ward, lấy trung bình cụm làm init của KMeans; sau khóa k, fit toàn train với n_init=1.', 'Người 2'],
      ['Vì sao không có High-Spenders?', 'InGamePurchases chỉ có 0/1. Cần số tiền, thời điểm và cửa sổ giao dịch để biết nhóm chi tiêu cao.', 'Người 1'],
      ['Tỷ lệ thắng/thua và tốc độ thu vật phẩm đâu?', 'Nguồn thiếu Wins/Losses, vật phẩm và thời gian theo dõi. Nhóm chỉ rõ phần chưa đáp ứng, không thay bằng biến khác rồi đổi tên.', 'Người 1'],
      ['Dữ liệu này là thật hay giả?', 'Đây là CSV Kaggle nguyên bản theo đề nhưng tác giả xác nhận là dữ liệu tổng hợp. Nhóm không tự tạo dữ liệu; kết luận giới hạn cho giáo dục.', 'Người 1'],
      ['Tại sao cần StandardScaler?', 'Khoảng cách Euclidean phụ thuộc thang đo. Scaler đưa năm biến về thang so sánh và chỉ fit trên train.', 'Người 1'],
      ['Tại sao Ward chỉ chạy trên mẫu?', 'Cách triển khai cây Ward cần bộ nhớ tăng bậc hai; lấy 4.000 train để kiểm soát chi phí, sau đó K-Means học toàn train.', 'Người 2'],
      ['Ward dự đoán holdout thế nào?', 'Ward không có predict tự nhiên. Dự án dùng tâm của cụm Ward để gán gần nhất; đây là mở rộng bằng tâm, đã ghi rõ trong bảng.', 'Người 2'],
      ['Silhouette mẫu có bằng điểm toàn bộ không?', 'Không. Dự án dùng cùng mẫu 2.000 để so sánh nhất quán, ghi kích thước mẫu và không gọi là điểm đầy đủ trên 40.034 người.', 'Người 2'],
      ['Hai cột thời lượng mâu thuẫn thì làm gì?', f'Không đổi thành giờ/tuần tùy ý. Báo cáo độ nhạy bỏ PlayTimeHours: ARI {s["feature_sensitivity"]["ari_vs_main"]:.4f}; cần xác minh với nguồn trước triển khai.', 'Người 1'],
      ['Kết hợp có chắc tốt hơn K-Means không?', 'Không. Chỉ số thực nghiệm mới quyết định so sánh; Ward khởi tạo vẫn có thể dẫn đến nghiệm kém hơn hoặc khác K-Means++.', 'Người 2'],
      ['Tại sao ARI ở đây không là Accuracy?', 'ARI so hai phân hoạch qua các seed, điều chỉnh mức trùng do ngẫu nhiên và bỏ qua số hiệu cụm. Không dùng nhãn đúng để tính.', 'Người 2'],
      ['Ưu đãi này tăng doanh thu bao nhiêu?', 'Chưa đo được. Cần A/B test phân ngẫu nhiên trong mỗi cụm và số tiền giao dịch; không suy ra uplift từ tỷ lệ có mua.', 'Người 2']]
    table(doc,'Bảng 1. Câu hỏi và cách trả lời',['Câu hỏi','Trả lời gợi ý','Người trả lời'],qa,
          'Nếu đổi phân công, sửa đồng thời lời chuyển lượt ở slide 7, Notes và cột người trả lời.')
    chapter(doc,'Bản ghi nhớ để ôn nhanh')
    for i,(title,bullets,img,notes) in enumerate(content,1):
        doc.add_heading(f'{i}. {title}',2)
        para(doc,'; '.join(bullets[:2]))
    doc.save(D/'Bai_noi_va_Hoi_dap.docx')


def build_readme(s):
    text=f'''# Gamer Behavior Clustering & Player Profiling

Dự án môn Khai phá dữ liệu, viết bằng tiếng Việt. Đọc báo cáo Word trong deliverables/.

## Chạy lại

Yêu cầu Python 3.13 trên máy có thể cài các phiên bản trong requirements.txt. Windows PowerShell:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe gamer_clustering.py
.\\.venv\\Scripts\\python.exe build_deliverables.py
```

Linux/macOS dùng `.venv/bin/python` thay cho `.\\.venv\\Scripts\\python.exe`.
Đã chạy thực tế với Python {s['python']}; chưa xác nhận trên mọi hệ điều hành.
Từ thư mục bất kỳ có thể chạy đường dẫn tuyệt đối đến script vì dữ liệu được định vị theo __file__.

## Đầu vào và nguồn

CSV nguyên bản: data/online_gaming_behavior_dataset.csv.
Tác giả: Rabie El Kharoua, Predict Online Gaming Behavior Dataset, version 1 (2024).
Nguồn: {SOURCE}
Giấy phép: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ . Dữ liệu được đóng gói lại cùng ghi nguồn; không thay đổi CSV nguồn.
Metadata: data/dataset_card.json và data/metadata.json. Nguồn ghi rõ **synthetic** cho giáo dục.
SHA-256 CSV: `{s['data_sha256']}`.

Không có wins/losses, vật phẩm theo thời gian, MMR/Elo hoặc số tiền mua.
PlayerLevel = tiến trình; AchievementsUnlocked = thành tích tích lũy; InGamePurchases = 0/1.
Không thể đo tỷ lệ thắng/thua, tốc độ thu vật phẩm, kỹ năng thật hay High-Spenders từ CSV này.
PlayTimeHours và AvgSessionDurationMinutes mâu thuẫn về ngữ nghĩa nguồn; có kiểm tra độ nhạy bỏ PlayTimeHours.
Không tự sinh dữ liệu mới. Dùng đúng nguồn đề giao, công bố giới hạn dữ liệu tổng hợp.

## Thiết kế thực nghiệm

- {s['rows']:,} dòng; train {s['n_train']:,}, holdout {s['n_holdout']:,}; seed 42.
- Năm biến: {', '.join(s['features'])}.
- Pipeline trung vị + StandardScaler fit train; không fit holdout.
- So KMeans++ (20 khởi tạo), Agglomerative Ward và Ward → tâm → KMeans.
- Chọn k=2…8 trên cùng mẫu {s['n_ward_sample']:,} train bằng tổng hạng Silhouette giảm, DBI tăng; hòa ưu tiên Silhouette rồi k nhỏ.
- Chọn k riêng mỗi phương pháp. Ward_KMeans là phương pháp chính xác định trước theo đề.
- Silhouette trên cùng mẫu 2.000 trong từng giai đoạn; DBI dùng toàn bộ tập đánh giá.
- Sau khóa k, K-Means và mô hình kết hợp fit toàn train. Ward thuần gán ngoài mẫu qua tâm, không coi là Ward chính xác trên toàn dữ liệu.
- Holdout không dùng chọn k/phương pháp. Không dùng EngagementLevel để học; mua hàng chỉ phân tích sau học.
- Hồ sơ mô tả toàn bộ dữ liệu. Đổi seed mẫu Ward 5 lần, so ARI trên cùng holdout; phân tích bỏ PlayTimeHours giữ k cố định.
- PCA chỉ minh họa, không dùng học cụm.

## Gán người chơi mới

CSV mới cần đủ năm cột đầu vào; có thể có PlayerID và cột khác.

```powershell
.\\.venv\\Scripts\\python.exe gamer_clustering.py --predict nguoi_choi_moi.csv
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

- {DOCS}
- https://docs.scipy.org/doc/scipy/reference/cluster.hierarchy.html

Chỉ số nội bộ chưa chứng minh hiệu quả thương mại; chiến lược trong báo cáo là giả thuyết A/B test.
'''
    (ROOT/'README.md').write_text(text,encoding='utf-8')


def main():
    D.mkdir(exist_ok=True)
    s=json.loads((O/'summary.json').read_text(encoding='utf-8'))
    audit=json.loads((O/'data_audit.json').read_text(encoding='utf-8'))
    p=pd.read_csv(O/'cluster_profiles.csv'); search=pd.read_csv(O/'model_selection.csv')
    ev=pd.read_csv(O/'holdout_metrics.csv'); stability=pd.read_csv(O/'stability.csv')
    build_report(s,p,search,ev,audit,stability)
    content=presentation_content(s,p,ev)
    build_slides(content); build_speech(content,s); build_readme(s)
    (D/'slide_content.json').write_text(json.dumps(content,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Đã tạo báo cáo, 18 slide có Notes và bài nói theo số liệu outputs/.')


if __name__=='__main__': main()
