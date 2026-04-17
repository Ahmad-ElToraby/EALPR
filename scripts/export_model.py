"""
Export YOLOv8 model to ONNX.
"""
import sys
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

def main():
    model_path = MODELS_DIR / "plate_detector.pt"
    if not model_path.exists():
        print("ERROR: models/plate_detector.pt not found.")
        sys.exit(1)
        
    model = YOLO(str(model_path))
    model.export(format="onnx", imgsz=640, simplify=True, opset=12)
    print("ONNX export complete.")
    try:
        model.export(format="tflite", imgsz=640)
        print("TFLite export complete.")
    except Exception as e:
        print(f"TFLite failed: {e}")

if __name__ == "__main__":
    main()
