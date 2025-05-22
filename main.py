import sys
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QDoubleSpinBox,
    QMessageBox, QCheckBox, QInputDialog
)
from PySide6.QtCore import Qt, QTimer
import platform
import subprocess
from capture_ocr import capture_and_ocr


class TimerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("經驗值效率計時器")
        self.resize(400, 350)

        self.start_time = None
        self.end_time = None
        self.start_value = None
        self.end_value = None
        self.target_seconds = 300
        self.remaining_time = 0
        self.image_dir = "screenshots"
        self.output_dir = "output"
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        self.results = []
        self.is_running = False
        self.save_screenshots = True

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_countdown)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.target_spin = QDoubleSpinBox()
        self.target_spin.setRange(0.1, 999.0)
        self.target_spin.setValue(self.target_seconds / 60)
        self.target_spin.setSuffix(" 分鐘")
        self.target_spin.setDecimals(2)

        self.save_screenshot_check = QCheckBox("儲存擷取圖片")
        self.save_screenshot_check.setChecked(False)  # 默認為不儲存
        self.save_screenshot_check.stateChanged.connect(self.toggle_save_screenshots)

        self.auto_save_check = QCheckBox("自動儲存結果")
        self.auto_save_check.setChecked(True)

        self.manual_input_check = QCheckBox("使用手動輸入數值（停用OCR）")
        self.manual_input_check.setChecked(False)

        self.info_label = QLabel("請設定目標分鐘數，點選「開始」")

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("開始（OCR）")
        self.end_btn = QPushButton("結束（OCR）")
        self.open_result_btn = QPushButton("打開結果")

        self.start_btn.clicked.connect(self.handle_start)
        self.end_btn.clicked.connect(self.handle_end)
        self.open_result_btn.clicked.connect(self.open_result_file)

        self.end_btn.setEnabled(False)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.end_btn)
        btn_layout.addWidget(self.open_result_btn)

        self.ocr_result_label = QLabel("")
        self.ocr_result_label.setAlignment(Qt.AlignCenter)

        self.countdown_label = QLabel("")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("font-size: 20px; color: red;")

        self.summary_label = QLabel("")
        self.summary_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.info_label)
        layout.addWidget(self.target_spin)
        layout.addWidget(self.auto_save_check)  # 自動儲存結果移到上面
        layout.addWidget(self.save_screenshot_check)
        layout.addWidget(self.manual_input_check)
        layout.addLayout(btn_layout)
        layout.addWidget(self.ocr_result_label)
        layout.addWidget(self.countdown_label)
        layout.addWidget(self.summary_label)

        self.setLayout(layout)
        self.setFixedSize(400, 350)  # 固定視窗大小，不能拉動

    def toggle_save_screenshots(self, state):
        self.save_screenshots = state == Qt.Checked

    def handle_start(self):
        if self.is_running:
            return
        self.target_seconds = int(self.target_spin.value() * 60)
        self.start_time = datetime.now()

        if self.manual_input_check.isChecked():
            val, ok = QInputDialog.getInt(self, "手動輸入", "請輸入開始數值：")
            if not ok:
                self.ocr_result_label.setText("開始數值：使用者取消輸入")
                return
            path = None
            timestamp = self.start_time.strftime("%H:%M:%S")
        else:
            val, path, timestamp = capture_and_ocr("start", self.image_dir, self, save_image=self.save_screenshots)

        if val is not None:
            self.start_value = val
            self.start_image = path
            self.start_stamp = timestamp
            self.notify("已記錄開始數值")
            self.ocr_result_label.setText(f"開始數值：{val}")
            self.is_running = True
            self.end_btn.setEnabled(True)
            self.start_btn.setEnabled(False)
            self.start_timer(self.target_seconds)
        else:
            self.ocr_result_label.setText("開始數值：OCR失敗或取消")

    def start_timer(self, seconds):
        self.timer.stop()
        self.remaining_time = seconds
        self.update_countdown()
        self.timer.start()

    def update_countdown(self):
        if self.remaining_time <= 0:
            self.timer.stop()
            self.countdown_label.setText("時間到！")
            self.time_up_notify()
        else:
            mins, secs = divmod(self.remaining_time, 60)
            self.countdown_label.setText(f"倒數：{int(mins):02d}:{int(secs):02d}")
            self.remaining_time -= 1

    def time_up_notify(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("時間到！")
        msg.setText("時間已到，請進行結束（OCR）操作")
        msg.setWindowFlag(Qt.WindowStaysOnTopHint)
        msg.exec()

    def handle_end(self):
        if not self.is_running:
            return
        self.timer.stop()
        self.countdown_label.setText("")
        self.end_time = datetime.now()

        if self.manual_input_check.isChecked():
            val, ok = QInputDialog.getInt(self, "手動輸入", "請輸入結束數值：")
            if not ok:
                self.ocr_result_label.setText("結束數值：使用者取消輸入")
                return
            path = None
            timestamp = self.end_time.strftime("%H:%M:%S")
        else:
            val, path, timestamp = capture_and_ocr("end", self.image_dir, self, save_image=self.save_screenshots)

        if val is not None:
            self.end_value = val
            self.end_image = path
            self.end_stamp = timestamp
            self.notify("已記錄結束數值")
            self.ocr_result_label.setText(f"結束數值：{val}")

            delta = self.end_value - self.start_value if self.start_value is not None else None
            remark, ok = QInputDialog.getText(self, "備註輸入", "請輸入備註：", text="地圖: 職業: 等級:")
            if ok and delta is not None:
                self.results.append({
                    "date": self.start_time.strftime("%Y-%m-%d %H:%M"),
                    "target": round(self.target_seconds / 60, 2),
                    "start_val": self.start_value,
                    "start_time": self.start_stamp,
                    "end_val": self.end_value,
                    "end_time": self.end_stamp,
                    "diff": delta,
                    "remark": remark
                })
                self.summary_label.setText(f"開始: {self.start_value} 結束: {self.end_value} 差值: {delta}")
                if self.auto_save_check.isChecked():
                    self.save_results()
            self.reset_state()
        else:
            self.ocr_result_label.setText("結束數值：OCR失敗或取消")

    def reset_state(self):
        self.is_running = False
        self.start_value = None
        self.end_value = None
        self.start_time = None
        self.end_time = None
        self.end_btn.setEnabled(False)
        self.start_btn.setEnabled(True)

    def save_results(self):
        if not self.results:
            return
        lines = []
        for r in self.results:
            line = f"{r['date']} | 目標:{r['target']}分 | 開始:{r['start_val']}({r['start_time']}) | " \
                   f"結束:{r['end_val']}({r['end_time']}) | 差值:{r['diff']} | 備註:{r['remark']}"
            lines.append(line)
        export_path = os.path.join(self.output_dir, "timer_results.txt")
        with open(export_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        # QMessageBox.information(self, "自動儲存成功", f"已自動儲存至：\n{export_path}")
        # 改為主視窗訊息顯示，不再彈窗
        self.info_label.setText(f"已自動儲存至：{export_path}")

    def open_result_file(self):
        export_path = os.path.join(self.output_dir, "timer_results.txt")
        self.open_file_location(os.path.abspath(export_path))

    def notify(self, message):
        self.info_label.setText(message)

    def open_file_location(self, filepath):
        if platform.system() == "Windows":
            subprocess.run(f'explorer /select,"{filepath}"')
        elif platform.system() == "Darwin":
            subprocess.run(["open", "-R", filepath])
        else:
            subprocess.run(["xdg-open", os.path.dirname(filepath)])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimerApp()
    window.show()
    sys.exit(app.exec())
