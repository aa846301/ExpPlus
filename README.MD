# ExpPlus

用於計算每多少分鐘經驗值用的計算機

支援功能
* 截圖OCR
* 手動輸入
* 儲存截圖
* 文本輸出結果

## 使用說明
1. release 下載最新版本
2. 解壓縮檔案
3. 雙擊ExpPlus.exe
4. 設定需要計時的時間,默認五分鐘
5. 按下開始
6. 框選畫面上的經驗值數字
7. 檢查是否正確,確認後,按下OK
8. 計時結束後,按下結束
9. 框選經驗值數字

Done!

## 環境建構 (windows)
Python Version = 3.12.4
```
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

```




## pyinstaller 打包命令
```powershell
pyinstaller --noconfirm --onefile --windowed  --name ExpPlus -F main.py --add-data=".\\.venv\\Lib\\site-packages\\onnxruntime\\capi\\onnxruntime_providers_shared.dll;./onnxruntime/capi" --add-data=".\\.venv\\Lib\\site-packages\\ddddocr\\common.onnx;./ddddocr" --add-data=".\\.venv\\Lib\\site-packages\\ddddocr\\common_old.onnx;./ddddocr"
```
