"""
Evaluate trained YOLOv8 plate detector on test set.
"""
import sys
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
DATASET_YAML = BASE_DIR / "dataset" / "data.yaml"

def main():
    model_path = MODELS_DIR / "plate_detector.pt"
    if not model_path.exists():
        print("ERROR: models/plate_detector.pt not found. Train first!")
        sys.exit(1)
    
    model = YOLO(str(model_path))
    metrics = model.val(
        data=str(DATASET_YAML), split="test", imgsz=640,
        project=str(MODELS_DIR), name="evaluation", exist_ok=True
    )
    print("=" * 60)
    print(f"mAP@50:    {metrics.box.map50:.4f}")
    print(f"mAP@50-95: {metrics.box.map:.4f}")
    print(f"Precision: {metrics.box.mp:.4f}")
    print(f"Recall:    {metrics.box.mr:.4f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
