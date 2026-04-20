"""
Inference Pipeline
"""
import cv2, numpy as np, base64, time, sys, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.ocr_engine import extract_text, sanitize_plate_text
from src.feature_extractor import extract_features
from src.classifier import classify_governorate
from src.database import init_db, save_scan

init_db()

_detector = None
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

def get_detector():
    global _detector
    if _detector is None:
        from ultralytics import YOLO
        mp = MODELS_DIR / "plate_detector.pt"
        if not mp.exists():
            print("WARNING: Custom model not found. Using pretrained YOLOv8n.")
            _detector = YOLO("yolov8n.pt")
        else:
            _detector = YOLO(str(mp))
    return _detector

def enhance_plate_crop(img):
    # Step 1: Upscale if too small
    h, w = img.shape[:2]
    if w < 300:
        scale = 300 / w
        img = cv2.resize(img, (int(w * scale), int(h * scale)),
                        interpolation=cv2.INTER_CUBIC)
    
    # Step 2: Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Step 3: CLAHE adaptive contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Step 4: Sharpen
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    # Step 5: Convert back to BGR for PaddleOCR
    return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)

def process_image(img, conf_th=0.25):
    st = time.time()
    if img is None: return {"error": "Invalid image"}
    det = get_detector()
    if not det: return {"error": "No model loaded"}
    
    results, plates_info = det(img, conf=conf_th, verbose=False), []
    
    all_boxes = []
    for r in results:
        all_boxes.extend(r.boxes)
        
    if all_boxes:
        # Focus exclusively on the main plate (largest area in the picture)
        main_box = max(all_boxes, key=lambda b: (b.xyxy[0][2] - b.xyxy[0][0]) * (b.xyxy[0][3] - b.xyxy[0][1]))
        
        x1, y1, x2, y2 = map(int, main_box.xyxy[0].cpu().numpy())
        px1, py1 = max(0, int(x1 - (x2-x1)*0.10)), max(0, int(y1 - (y2-y1)*0.10))
        px2, py2 = min(img.shape[1], int(x2 + (x2-x1)*0.10)), min(img.shape[0], int(y2 + (y2-y1)*0.10))
        
        crop = img[py1:py2, px1:px2]
        if crop.size > 0:
            enhanced_crop = enhance_plate_crop(crop)
            feat, ocr = extract_features(crop), extract_text(enhanced_crop)
            
            raw_text = ocr.get("full_text", "")
            sanitized = sanitize_plate_text(raw_text, "arabic")
            gov = classify_governorate(sanitized)
            
            cls = {
                "governorate": gov,
                "vehicle_type": feat.get("vehicle_type", "Unknown")
            }
            
            bbox = [x1, y1, x2, y2]
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, f"{cls['vehicle_type']} | {cls['governorate']}", (x1, y1-10), 0, 0.5, (0,0,0), 3)
            cv2.putText(img, f"{cls['vehicle_type']} | {cls['governorate']}", (x1, y1-10), 0, 0.5, (0,255,0), 1)
            
            plate = {**ocr, **feat, **cls, "bbox": bbox, "plate_text": sanitized}
            plates_info.append(plate)
            
            try:
                save_scan(
                    plate_text=plate.get("plate_text", ""),
                    governorate=plate.get("governorate", "Unknown"),
                    vehicle_type=plate.get("vehicle_type", "Unknown"),
                    confidence=plate.get("confidence", 0.0),
                    color_code=plate.get("color_code", "")
                )
            except Exception as e:
                logging.error(f"Database error while saving scan: {e}")
            
    _, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return {
        "plates": plates_info, "num_plates_detected": len(plates_info),
        "processing_time_ms": round((time.time() - st) * 1000, 1),
        "annotated_image": base64.b64encode(buf).decode('utf-8')
    }

def process_base64_image(b64, conf=0.25):
    if ',' in b64: b64 = b64.split(',')[1]
    img = cv2.imdecode(np.frombuffer(base64.b64decode(b64), np.uint8), cv2.IMREAD_COLOR)
    return process_image(img, conf)
