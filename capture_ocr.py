import os
import sys
import re
from datetime import datetime
import numpy as np
import cv2
import mss
import ddddocr
from PySide6.QtWidgets import QInputDialog, QMessageBox
import ctypes

ocr = ddddocr.DdddOcr()
ocr.set_ranges(0)

def extract_digits(text):
    digits = re.findall(r'\d+', text)
    print(f"[OCR] 擷取的數字：{digits}")
    return digits[0] if digits else ''

def get_mouse_position():
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def custom_select_roi(window_name, img, screen_left, screen_top):
    roi = [0, 0, 0, 0]
    selecting = [False]
    start_point = [0, 0]
    end_point = [0, 0]
    clone = img.copy()
    done = [False]

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            selecting[0] = True
            start_point[0], start_point[1] = x, y
            end_point[0], end_point[1] = x, y
        elif event == cv2.EVENT_MOUSEMOVE and selecting[0]:
            end_point[0], end_point[1] = x, y
        elif event == cv2.EVENT_LBUTTONUP and selecting[0]:
            selecting[0] = False
            end_point[0], end_point[1] = x, y
            roi[0] = min(start_point[0], end_point[0])
            roi[1] = min(start_point[1], end_point[1])
            roi[2] = abs(end_point[0] - start_point[0])
            roi[3] = abs(end_point[1] - start_point[1])
            done[0] = True

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.moveWindow(window_name, screen_left, screen_top)
    cv2.setMouseCallback(window_name, mouse_callback)

    while True:
        display = clone.copy()
        if selecting[0] or done[0]:
            cv2.rectangle(display, tuple(start_point), tuple(end_point), (0, 255, 0), 2)
        cv2.imshow(window_name, display)
        key = cv2.waitKey(1) & 0xFF
        if done[0]:
            break
        if key == 27:  # ESC
            roi = [0, 0, 0, 0]
            break
    cv2.destroyWindow(window_name)
    return tuple(roi)

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout

def ocr_correction_dialog(parent, raw_text, digit_text):
    class CorrectionDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("OCR 校正")
            self.result = None
            self.retry = False
            layout = QVBoxLayout()
            layout.addWidget(QLabel(f"OCR 辨識為：{raw_text}"))
            self.input = QLineEdit()
            self.input.setText(digit_text)
            layout.addWidget(self.input)
            btn_layout = QHBoxLayout()
            ok_btn = QPushButton("確定")
            retry_btn = QPushButton("重新截圖")
            cancel_btn = QPushButton("取消")
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(retry_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)
            self.setLayout(layout)
            ok_btn.clicked.connect(self.accept)
            retry_btn.clicked.connect(self.retry_action)
            cancel_btn.clicked.connect(self.reject)
        def accept(self):
            self.result = self.input.text()
            super().accept()
        def retry_action(self):
            self.retry = True
            super().reject()
    dialog = CorrectionDialog(parent)
    result = dialog.exec()
    return dialog.result, result == 1, dialog.retry


def capture_and_ocr(label, image_dir, parent=None, save_image=True):
    while True:
        with mss.mss() as sct:
            monitors = sct.monitors
            print(f"[資訊] 偵測到螢幕數量：{len(monitors)-1}")
            mouse_x, mouse_y = get_mouse_position()
            monitor = None
            for mon in monitors[1:]:
                if (mon['left'] <= mouse_x < mon['left'] + mon['width'] and
                    mon['top'] <= mouse_y < mon['top'] + mon['height']):
                    monitor = mon
                    break
            if monitor is None:
                monitor = monitors[1]  # fallback
            print(f"[資訊] 滑鼠座標: ({mouse_x}, {mouse_y})，使用螢幕：{monitor}")

            img_np = np.array(sct.grab(monitor))
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)

            print("[資訊] 開啟 ROI 選取視窗 (Esc 或關閉視窗取消)")
            r = custom_select_roi("Select ROI (Esc or close to cancel)", img_bgr, monitor['left'], monitor['top'])
            print(f"[事件] ROI 回傳值：{r}")
            if r[2] == 0 or r[3] == 0:
                print("[錯誤] 使用者未選擇有效區域")
                return None, None, None

            x, y, w, h = r
            cropped = img_bgr[y:y + h, x:x + w]
            print(f"[資訊] 裁切區域：x={x}, y={y}, w={w}, h={h}")

            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_path = None
            if save_image:
                os.makedirs(image_dir, exist_ok=True)
                img_path = os.path.join(image_dir, f"{now}_{label}.png")
                cv2.imwrite(img_path, cropped)
                print(f"[儲存] 圖片儲存於：{img_path}")

            try:
                _, img_encoded = cv2.imencode(".png", cropped)
                raw_text = ocr.classification(img_encoded.tobytes()).strip()
                print(f"[OCR] 原始文字：{raw_text}")
                digit_text = extract_digits(raw_text)
            except Exception as e:
                print(f"[錯誤] OCR 發生錯誤：{e}")
                if parent:
                    QMessageBox.critical(parent, "OCR 錯誤", str(e))
                return None, None, None

            if parent:
                corrected, ok, retry = ocr_correction_dialog(parent, raw_text, digit_text)
                if retry:
                    continue  # 重新截圖
                if ok and corrected.strip().isdigit():
                    return int(corrected.strip()), img_path, now
                else:
                    QMessageBox.warning(parent, "輸入錯誤", "請輸入正確的數字。")
                    return None, None, None
            else:
                try:
                    return int(digit_text), img_path, now
                except Exception:
                    return None, None, None
