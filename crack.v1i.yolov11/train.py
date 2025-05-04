# train.py
import os
from ultralytics import YOLO

# （可選）繞過 Windows 下的 OpenMP 重複載入問題
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def main():
    # 檢查 CUDA 是否可用
    import torch
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("Using GPU:", torch.cuda.get_device_name(0))
    else:
        print("CUDA not available, using CPU.")

    # 載入預訓練權重
    model = YOLO("yolo11s.pt")  # 或改成 yolo11n.pt, yolo11m.pt 等

    # 開始訓練
    model.train(
        data="data.yaml",      # dataset 配置
        epochs=100,            # 訓練輪數
        imgsz=640,             # 輸入尺寸
        batch=16,              # batch size
        device=0,              # GPU 編號，若要用 CPU 填 "cpu"
        workers=0,             # Windows 下建議設 0
        project="runs",        # 輸出資料夾
        name="crack_detector", # 輸出子資料夾名稱
        exist_ok=True          # 若 runs/crack_detector 已存在則覆寫
    )

if __name__ == "__main__":
    main()
