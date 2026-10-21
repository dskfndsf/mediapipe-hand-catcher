# Hand Catcher & Shield - MediaPipe Interactive Game

Trò chơi tương tác qua camera thời gian thực được xây dựng bằng **Python**, **OpenCV** và **MediaPipe Hands**. Người chơi sử dụng vị trí và cử chỉ bàn tay để điều khiển thanh hứng vật phẩm và kích hoạt khiên chống bom.

## 1. Danh sách các thư viện cần thiết
* Python 3.9 - 3.11
* `opencv-python` (Xử lý hình ảnh, giao diện trò chơi và luồng camera)
* `mediapipe` (Trích xuất 21 điểm landmark trên bàn tay)
* `numpy` (Tính toán toán học)

## 2. Hướng dẫn cài đặt và chạy chương trình

**Bước 1: Clone repository về máy**
```bash
git clone https://github.com/<username-cua-ban>/mediapipe-hand-catcher.git
cd mediapipe-hand-catcher
```

**Bước 2: Cài đặt thư viện**
```bash
pip install -r requirements.txt
```

**Bước 3: Chạy chương trình**
```bash
python main.py
```

## 3. Hướng dẫn sử dụng Game
* **Di chuyển thanh hứng (Catcher):** Đưa một bàn tay lên trước camera và di chuyển sang trái/phải để điều khiển thanh hứng ở cuối màn hình.
* **Chế độ Hứng Sao (Open Hand - Xòe bàn tay):** Giữ bàn tay mở để thu thập các quả cầu màu xanh lá (`+1` điểm).
* **Chế độ Khiên Chắn (Fist - Nắm bàn tay):** Khi thấy quả bom màu đỏ (`X`) rơi xuống mà không kịp né, hãy **nắm bàn tay lại** để bật khiên màu vàng giúp vô hiệu hóa bom (lưu ý: khi đang bật khiên bạn cũng không thể nhận điểm từ sao xanh).
* **Điều kiện Thắng / Thua:**
  * Đạt đủ **25 điểm** để chiến thắng.
  * Bị bom nổ trúng **3 lần** (hết 3 mạng) sẽ thua cuộc.
* **Phím tắt:** Nhấn `R` để chơi lại khi kết thúc ván, nhấn `Q` để thoát chương trình.

## 4. Quy trình xử lý của chương trình
`Camera` -> `MediaPipe Hands (21 Landmarks)` -> `Thuật toán lọc nhiễu EMA & Nhận diện cử chỉ Nắm/Mở tay & Kiểm tra va chạm Circle-AABB` -> `Game Hand Catcher & Shield`

## 5. Video Demo
* Link xem Video Demo: *(Cập nhật link Google Drive / YouTube Video Demo tại đây)*
