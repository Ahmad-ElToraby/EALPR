"""
YOLOv8 Training Script for License Plate Detection
"""
import sys
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_YAML = BASE_DIR / "dataset" / "data.yaml"
MODELS_DIR = BASE_DIR / "models"

def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if not DATASET_YAML.exists():
        print("ERROR: dataset/data.yaml not found. Run prepare_dataset.py first!")
        sys.exit(1)
    
    print("=" * 60)
    print("YOLOv8 License Plate Detector Training")
    print("=" * 60)
    
    model = YOLO("yolov8m.pt")
    results = model.train(
        data=str(DATASET_YAML),
        epochs=100, imgsz=640, batch=16, patience=15,
        save=True, project=str(MODELS_DIR), name="plate_detector",
        exist_ok=True, pretrained=True, optimizer="AdamW",
        lr0=0.001, lrf=0.01, warmup_epochs=3, augment=True,
        device="0" if _has_cuda() else "cpu", workers=0, verbose=True
    )
    
    best_model_src = MODELS_DIR / "plate_detector" / "weights" / "best.pt"
    best_model_dst = MODELS_DIR / "plate_detector.pt"
    if best_model_src.exists():
        import shutil
        shutil.copy2(str(best_model_src), str(best_model_dst))
    print(f"\nTraining complete! Best model: {best_model_dst}")

def _has_cuda():
    try:
        import torch
        return torch.cuda.is_available()
    except:
        return False

if __name__ == "__main__":
    main()
