"""
End-to-End Pipeline Test for EALPR
Loads a test image, runs the full pipeline, and prints all results.
Saves annotated output for visual verification.
"""
import sys, os, time, json
from pathlib import Path

# Fix Windows console encoding for Unicode/emoji output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Setup project path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

def test_model_loading():
    """Test 1: Verify the YOLO model loads correctly."""
    print("\n" + "=" * 60)
    print("TEST 1: Model Loading")
    print("=" * 60)
    
    model_path = BASE_DIR / "models" / "plate_detector.pt"
    if not model_path.exists():
        print(f"  [FAIL] Model not found at {model_path}")
        return False
    
    print(f"  [OK] Model file exists ({model_path.stat().st_size / 1024 / 1024:.1f} MB)")
    
    try:
        from ultralytics import YOLO
        model = YOLO(str(model_path))
        print(f"  [OK] Model loaded successfully")
        print(f"     Model type: {model.task}")
        print(f"     Class names: {model.names}")
        return True
    except Exception as e:
        print(f"  [FAIL] Could not load model: {e}")
        return False


def test_ocr_engine():
    """Test 2: Verify OCR engine initializes."""
    print("\n" + "=" * 60)
    print("TEST 2: OCR Engine (PaddleOCR)")
    print("=" * 60)
    
    try:
        from src.ocr_engine import get_reader
        reader = get_reader()
        print(f"  [OK] PaddleOCR initialized successfully")
        return True
    except Exception as e:
        print(f"  [FAIL] OCR engine failed: {e}")
        print(f"     Make sure paddleocr and paddlepaddle are installed:")
        print(f"     pip install paddleocr paddlepaddle")
        return False


def test_full_pipeline():
    """Test 3: Run full pipeline on test images."""
    print("\n" + "=" * 60)
    print("TEST 3: Full Pipeline (Detection -> OCR -> Classification)")
    print("=" * 60)
    
    import cv2
    from src.pipeline import process_image
    
    # Find test images
    test_images_dir = BASE_DIR / "dataset" / "test" / "images"
    if not test_images_dir.exists():
        print(f"  [FAIL] Test images directory not found: {test_images_dir}")
        return False
    
    test_images = sorted(test_images_dir.glob("*.jpg"))[:5]  # Test first 5
    if not test_images:
        print(f"  [FAIL] No test images found")
        return False
    
    print(f"  Testing on {len(test_images)} images...\n")
    
    total_detections = 0
    output_dir = BASE_DIR / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    for i, img_path in enumerate(test_images, 1):
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  [{i}] WARNING: Could not read: {img_path.name}")
            continue
        
        print(f"  [{i}] Processing: {img_path.name} ({img.shape[1]}x{img.shape[0]})")
        
        result = process_image(img.copy())
        
        if "error" in result:
            print(f"      [ERROR] {result['error']}")
            continue
        
        num_plates = result["num_plates_detected"]
        proc_time = result["processing_time_ms"]
        total_detections += num_plates
        
        print(f"      Time: {proc_time}ms")
        print(f"      Plates detected: {num_plates}")
        
        for j, plate in enumerate(result["plates"], 1):
            print(f"\n      --- Plate {j} ---")
            print(f"      Plate text:    {plate.get('plate_text', plate.get('full_text', 'N/A'))}")
            print(f"      Raw OCR text:  {plate.get('raw_text', 'N/A')}")
            print(f"      Letters:       {plate.get('letters', 'N/A')}")
            print(f"      Numbers:       {plate.get('numbers', 'N/A')}")
            print(f"      OCR Conf:      {plate.get('confidence', 0):.2%}")
            print(f"      Governorate:   {plate.get('governorate', '?')} ({plate.get('governorate_ar', '?')})")
            print(f"      Vehicle type:  {plate.get('vehicle_type', '?')} ({plate.get('vehicle_type_ar', '?')})")
            print(f"      Plate color:   {plate.get('plate_color', '?')}")
            print(f"      Layout:        {plate.get('layout', '?')}")
            print(f"      Overall Conf:  {plate.get('overall_confidence', 0):.2%}")
            print(f"      BBox:          {plate.get('bbox', 'N/A')}")
        
        # Save annotated image
        if result.get("annotated_image"):
            import base64, numpy as np
            img_data = base64.b64decode(result["annotated_image"])
            nparr = np.frombuffer(img_data, np.uint8)
            annotated = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            output_path = output_dir / f"result_{img_path.name}"
            cv2.imwrite(str(output_path), annotated)
            print(f"      Saved: {output_path}")
        
        print()
    
    print(f"\n  SUMMARY: {total_detections} plates detected across {len(test_images)} images")
    print(f"  Annotated results saved to: {output_dir}")
    
    if total_detections > 0:
        print(f"  [OK] Pipeline is WORKING!")
        return True
    else:
        print(f"  [FAIL] No plates detected - investigate model or images")
        return False


def test_api_endpoints():
    """Test 4: Verify API server starts and endpoints respond."""
    print("\n" + "=" * 60)
    print("TEST 4: API Server Check")
    print("=" * 60)
    
    try:
        from fastapi.testclient import TestClient
        from src.main import app
        client = TestClient(app)
        
        # Health check
        resp = client.get("/api/health")
        if resp.status_code == 200 and resp.json().get("status") == "healthy":
            print(f"  [OK] /api/health -> {resp.json()}")
        else:
            print(f"  [FAIL] /api/health failed: {resp.status_code}")
            return False
        
        # Frontend
        resp = client.get("/")
        if resp.status_code == 200:
            print(f"  [OK] / (frontend) -> served OK")
        else:
            print(f"  [WARN] / (frontend) -> {resp.status_code}")
        
        # Test detection with a real image
        import cv2
        test_img_dir = BASE_DIR / "dataset" / "test" / "images"
        test_imgs = sorted(test_img_dir.glob("*.jpg"))
        if test_imgs:
            img = cv2.imread(str(test_imgs[0]))
            _, buf = cv2.imencode('.jpg', img)
            from io import BytesIO
            resp = client.post(
                "/api/detect",
                files={"file": ("test.jpg", BytesIO(buf.tobytes()), "image/jpeg")}
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"  [OK] /api/detect -> {data['num_plates_detected']} plates in {data['processing_time_ms']}ms")
            else:
                print(f"  [FAIL] /api/detect -> {resp.status_code}: {resp.text[:200]}")
                return False
        
        return True
    except ImportError:
        print(f"  [WARN] httpx not installed (needed for TestClient). Install with: pip install httpx")
        print(f"     Skipping API test.")
        return True
    except Exception as e:
        print(f"  [FAIL] API test failed: {e}")
        return False


if __name__ == "__main__":
    print("EALPR End-to-End Pipeline Test")
    print("=" * 60)
    
    results = {}
    
    results["Model Loading"] = test_model_loading()
    results["OCR Engine"] = test_ocr_engine()
    results["Full Pipeline"] = test_full_pipeline()
    results["API Endpoints"] = test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status}  {test_name}")
    
    all_passed = all(results.values())
    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED! Pipeline is ready.")
        print(f"\nTo run the server for your phone:")
        print(f"  cd {BASE_DIR}")
        print(f"  python -m src.main --tunnel")
    else:
        print("Some tests failed. Fix the issues above and re-run.")
    
    sys.exit(0 if all_passed else 1)
