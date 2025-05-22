# ExpPlus

用於計算楓之谷每多少分鐘經驗值用的計算機
支援截圖以及手動輸入
可以截圖 然後識別經驗值數字 然後 開始計時 時間到彈出視窗 再截一次經驗值可以算出差值

## pyinstaller 打包命令
```powershell
pyinstaller --noconfirm --onefile --windowed  --name ExpPlus -F main.py --add-data=".\\.venv\\Lib\\site-packages\\onnxruntime\\capi\\onnxruntime_providers_shared.dll;./onnxruntime/capi" --add-data=".\\.venv\\Lib\\site-packages\\ddddocr\\common.onnx;./ddddocr" --add-data=".\\.venv\\Lib\\site-packages\\ddddocr\\common_old.onnx;./ddddocr"
```
