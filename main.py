import cv2
import mediapipe as mp
import numpy as np
import random
import time
import math

# Khởi tạo MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Cấu hình màn hình và thông số Game
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720
CATCHER_WIDTH = 130
CATCHER_HEIGHT = 24
CATCHER_Y = WINDOW_HEIGHT - 60
EMA_ALPHA = 0.35  # Hệ số làm mượt chuyển động (Exponential Moving Average)
WIN_SCORE = 25    # Điểm mục tiêu để chiến thắng
INITIAL_LIVES = 3

class FallingObject:
    """Lớp đại diện cho vật phẩm rơi từ trên xuống (Sao điểm thưởng hoặc Bom)."""
    def __init__(self, speed_multiplier=1.0):
        self.radius = 22
        self.x = random.randint(self.radius + 20, WINDOW_WIDTH - self.radius - 20)
        self.y = -self.radius
        # 70% là vật phẩm cộng điểm (type='star'), 30% là bom trừ mạng (type='bomb')
        self.obj_type = 'star' if random.random() < 0.7 else 'bomb'
        base_speed = random.uniform(5.0, 8.5)
        self.speed = base_speed * speed_multiplier

    def update(self):
        self.y += self.speed

    def draw(self, frame):
        if self.obj_type == 'star':
            # Vẽ quả cầu xanh lá (Vật phẩm cộng điểm)
            cv2.circle(frame, (int(self.x), int(self.y)), self.radius, (0, 230, 118), -1)
            cv2.circle(frame, (int(self.x), int(self.y)), self.radius, (255, 255, 255), 2)
            cv2.putText(frame, "+1", (int(self.x) - 14, int(self.y) + 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        else:
            # Vẽ quả bom đỏ (Vật phẩm gây sát thương)
            cv2.circle(frame, (int(self.x), int(self.y)), self.radius, (0, 50, 255), -1)
            cv2.circle(frame, (int(self.x), int(self.y)), self.radius, (0, 215, 255), 2)
            cv2.putText(frame, "X", (int(self.x) - 8, int(self.y) + 7),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)


def is_hand_closed(landmarks):
    """
    Thuật toán nhận diện cử chỉ nắm bàn tay (Fist) dựa trên khoảng cách Euclid.
    So sánh khoảng cách từ đầu 4 ngón tay (8, 12, 16, 20) tới cổ tay (0)
    so với khoảng cách từ khớp gốc ngón tay (5, 9, 13, 17) tới cổ tay (0).
    """
    wrist = landmarks[0]
    finger_tips = [8, 12, 16, 20]
    finger_mcps = [5, 9, 13, 17]
    folded_count = 0

    for tip_idx, mcp_idx in zip(finger_tips, finger_mcps):
        tip = landmarks[tip_idx]
        mcp = landmarks[mcp_idx]
        dist_tip_wrist = math.hypot(tip.x - wrist.x, tip.y - wrist.y)
        dist_mcp_wrist = math.hypot(mcp.x - wrist.x, mcp.y - wrist.y)
        if dist_tip_wrist < dist_mcp_wrist * 1.15:
            folded_count += 1

    return folded_count >= 3  # Nếu từ 3 ngón trở lên gập vào lòng bàn tay -> Nắm tay


def check_collision(obj, catcher_x, catcher_y, catcher_w, catcher_h):
    """
    Thuật toán phát hiện va chạm giữa Hình tròn (vật thể rơi) và Hình chữ nhật (Catcher).
    Tìm điểm gần nhất trên hình chữ nhật tới tâm hình tròn, sau đó tính khoảng cách.
    """
    half_w = catcher_w / 2
    half_h = catcher_h / 2
    rect_left = catcher_x - half_w
    rect_right = catcher_x + half_w
    rect_top = catcher_y - half_h
    rect_bottom = catcher_y + half_h

    closest_x = max(rect_left, min(obj.x, rect_right))
    closest_y = max(rect_top, min(obj.y, rect_bottom))

    distance = math.hypot(obj.x - closest_x, obj.y - closest_y)
    return distance <= obj.radius


def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_HEIGHT)

    catcher_x = WINDOW_WIDTH // 2
    score = 0
    lives = INITIAL_LIVES
    objects = []
    last_spawn_time = time.time()
    game_over = False
    game_won = False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Lật ngang khung hình để tạo hiệu ứng gương tự nhiên cho người chơi
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (WINDOW_WIDTH, WINDOW_HEIGHT))
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Trích xuất dữ liệu bàn tay từ MediaPipe
        results = hands.process(rgb_frame)
        shield_active = False

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Lấy landmark số 9 (khớp gốc ngón giữa - tâm bàn tay) để điều khiển vị trí ngang
            raw_x = hand_landmarks.landmark[9].x * WINDOW_WIDTH
            # Làm mượt vị trí bằng bộ lọc EMA để chống rung
            catcher_x = int(EMA_ALPHA * raw_x + (1 - EMA_ALPHA) * catcher_x)
            catcher_x = max(CATCHER_WIDTH // 2, min(WINDOW_WIDTH - CATCHER_WIDTH // 2, catcher_x))

            # Kiểm tra trạng thái nắm tay để kích hoạt Khiên chắn bom (Shield)
            shield_active = is_hand_closed(hand_landmarks.landmark)

        if not game_over and not game_won:
            # Tăng độ khó theo điểm số
            speed_multiplier = 1.0 + (score * 0.04)
            spawn_interval = max(0.45, 1.1 - (score * 0.02))

            if time.time() - last_spawn_time > spawn_interval:
                objects.append(FallingObject(speed_multiplier))
                last_spawn_time = time.time()

            # Cập nhật vị trí và kiểm tra va chạm
            remaining_objects = []
            for obj in objects:
                obj.update()
                if check_collision(obj, catcher_x, CATCHER_Y, CATCHER_WIDTH, CATCHER_HEIGHT):
                    if obj.obj_type == 'star':
                        if not shield_active:
                            score += 1  # Chỉ hứng được sao khi mở lòng bàn tay
                    elif obj.obj_type == 'bomb':
                        if not shield_active:
                            lives -= 1  # Bị trừ mạng nếu không nắm tay bật khiên
                elif obj.y - obj.radius <= WINDOW_HEIGHT:
                    remaining_objects.append(obj)

            objects = remaining_objects

            if score >= WIN_SCORE:
                game_won = True
            elif lives <= 0:
                game_over = True

        # Vẽ các vật phẩm rơi
        for obj in objects:
            obj.draw(frame)

        # Vẽ thanh Catcher (Xanh dương khi mở tay hứng sao, Vàng cam khi nắm tay bật khiên)
        catcher_color = (0, 191, 255) if shield_active else (255, 180, 0)
        top_left = (int(catcher_x - CATCHER_WIDTH // 2), int(CATCHER_Y - CATCHER_HEIGHT // 2))
        bottom_right = (int(catcher_x + CATCHER_WIDTH // 2), int(CATCHER_Y + CATCHER_HEIGHT // 2))
        cv2.rectangle(frame, top_left, bottom_right, catcher_color, -1)
        cv2.rectangle(frame, top_left, bottom_right, (255, 255, 255), 2)

        mode_text = "SHIELD ON (Fist)" if shield_active else "CATCH MODE (Open Hand)"
        cv2.putText(frame, mode_text, (top_left[0] - 20, top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, catcher_color, 2)

        # Hiển thị HUD (Điểm số & Mạng sống)
        cv2.rectangle(frame, (15, 15), (340, 110), (30, 30, 30), -1)
        cv2.putText(frame, f"Score: {score}/{WIN_SCORE}", (30, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 128), 2)
        cv2.putText(frame, f"Lives: {lives}", (30, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 100, 255), 2)

        # Màn hình Thắng / Thua
        if game_won or game_over:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (WINDOW_WIDTH, WINDOW_HEIGHT), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.65, frame, 0.35, 0)

            status_text = "YOU WIN!" if game_won else "GAME OVER!"
            status_color = (0, 255, 128) if game_won else (0, 60, 255)
            cv2.putText(frame, status_text, (WINDOW_WIDTH // 2 - 160, WINDOW_HEIGHT // 2 - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 2.0, status_color, 4)
            cv2.putText(frame, "Press 'R' to Restart or 'Q' to Quit",
                        (WINDOW_WIDTH // 2 - 230, WINDOW_HEIGHT // 2 + 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2)

        cv2.imshow("MediaPipe Hand Catcher & Shield", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r') and (game_over or game_won):
            score = 0
            lives = INITIAL_LIVES
            objects.clear()
            game_over = False
            game_won = False

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
