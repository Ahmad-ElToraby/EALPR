import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

"""
Arabic OCR Engine for Egyptian License Plates
Uses EasyOCR with preprocessing optimized for plate text.
"""
import cv2
import numpy as np
import logging

PERMITTED_LATIN = set("ABGDRSCTEFKLMNHWY123456789")
PERMITTED_ARABIC = set("أبجدرسصطعفقلمنهوى١٢٣٤٥٦٧٨٩")

ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
WESTERN_TO_ARABIC = {str(i): ARABIC_DIGITS[i] for i in range(10)}
ARABIC_TO_WESTERN = {ARABIC_DIGITS[i]: str(i) for i in range(10)}
VALID_PLATE_LETTERS = set("ا ب ج د ه و ز ح ط ي ك ل م ن س ع ف ص ق ر".split())

_reader = None

def get_reader():
    global _reader
    if _reader is None:
        from paddleocr import PaddleOCR
        import logging
        logging.getLogger('ppocr').setLevel(logging.ERROR)
        logging.getLogger('paddleocr').setLevel(logging.ERROR)
        try:
            _reader = PaddleOCR(lang='en')
        except Exception as e:
            print(f"PaddleOCR init failed: {e}")
            _reader = None
    return _reader

def preprocess_plate_image(plate_img):
    if plate_img is None or plate_img.size == 0: return None
    target_height = 96
    h, w = plate_img.shape[:2]
    if h == 0: return None
    scale = target_height / h
    target_width = int(w * scale)
    if target_width == 0: return None
    
    resized = cv2.resize(plate_img, (target_width, target_height))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) if len(resized.shape) == 3 else resized
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    enhanced = clahe.apply(denoised)
    
    return {'original': resized, 'gray': gray, 'thresh': thresh, 'enhanced': enhanced}

def sanitize_plate_text(text: str, script: str) -> str:
    permitted = PERMITTED_LATIN if script == "latin" else PERMITTED_ARABIC
    cleaned = []
    stripped_count = 0
    for char in text:
        if char in permitted or char.isspace():
            cleaned.append(char)
        else:
            stripped_count += 1
            
    if stripped_count > 2:
        logging.warning(f"OCR Noise detected: stripped {stripped_count} characters from '{text}'")
        
    return "".join(cleaned)

def cross_verify(latin_text: str, arabic_text: str) -> bool:
    ar_to_lat = {
        'أ': 'A', 'ب': 'B', 'ج': 'G', 'د': 'D', 'ر': 'R', 'س': 'S', 'ص': 'C', 'ط': 'T', 
        'ع': 'E', 'ف': 'F', 'ق': 'K', 'ل': 'L', 'م': 'M', 'ن': 'N', 'هـ': 'H', 'و': 'W', 'ى': 'Y'
    }
    num_map = {'١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'}
    
    transliterated = []
    for char in arabic_text:
        if char in ar_to_lat:
            transliterated.append(ar_to_lat[char])
        elif char in num_map:
            transliterated.append(num_map[char])
        elif char.isspace():
            transliterated.append(char)
            
    transliterated_str = "".join(transliterated).replace(" ", "")
    latin_clean = latin_text.replace(" ", "")
    
    match = (transliterated_str == latin_clean)
    if not match:
        logging.warning(f"Cross verification failed: Transliterated '{transliterated_str}' != Latin '{latin_clean}'")
        
    return match

def extract_text(plate_img):
    if plate_img is None or plate_img.size == 0: return _empty_result()
    reader = get_reader()
    if reader is None: return _empty_result()
    preprocessed = preprocess_plate_image(plate_img)
    if not preprocessed: return _empty_result()
    
    best_text, best_confidence = None, 0
    
    for version in ['original', 'enhanced', 'thresh']:
        img_for_ocr = cv2.cvtColor(preprocessed[version], cv2.COLOR_GRAY2BGR) if len(preprocessed[version].shape) == 2 else preprocessed[version]
        try:
            results = reader.ocr(img_for_ocr)
            
            boxes_collected = []
            if results and results[0]:
                for line in results[0]:
                    try:
                        if isinstance(line, list) and len(line) >= 2:
                            bbox = line[0]
                            text_info = line[1]
                            if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                                text, conf = text_info[0], float(text_info[1])
                            elif isinstance(text_info, str):
                                text, conf = text_info, 1.0
                            else: continue
                            if len(str(text).strip()) > 0:
                                boxes_collected.append((bbox, str(text).strip(), float(conf)))
                    except Exception:
                        continue
            
            if not boxes_collected: continue
            
            # Sort boxes RTL
            boxes_with_centers = []
            for box in boxes_collected:
                bbox, text, conf = box
                if not bbox or not isinstance(bbox, list) or len(bbox) != 4:
                    boxes_with_centers.append((0, 0, box))
                else:
                    try:
                        cx = sum(p[0] for p in bbox) / 4.0
                        cy = sum(p[1] for p in bbox) / 4.0
                        boxes_with_centers.append((cx, cy, box))
                    except Exception:
                        boxes_with_centers.append((0, 0, box))
            
            # Split into Meta text (top 40%) and Main text (bottom 60%) to avoid "Egypt" pollution
            # target_height is 96. So threshold is 38.4 pixels.
            meta_boxes, main_boxes = [], []
            for item in boxes_with_centers:
                cx, cy, box = item
                if cy < 96 * 0.40:
                    meta_boxes.append(item)
                else:
                    main_boxes.append(item)
            
            if not main_boxes: continue
            
            sorted_by_y = sorted(main_boxes, key=lambda b: b[1])
            lines_list = []
            current_line = []
            last_y = None
            for item in sorted_by_y:
                cx, cy, box = item
                if last_y is None:
                    current_line.append(item)
                    last_y = cy
                elif abs(cy - last_y) < 15: # Y tolerance for same line
                    current_line.append(item)
                    last_y = (last_y * (len(current_line)-1) + cy) / len(current_line)
                else:
                    lines_list.append(current_line)
                    current_line = [item]
                    last_y = cy
            if current_line: lines_list.append(current_line)
            
            final_text_parts = []
            total_conf = 0.0
            for line in lines_list:
                line.sort(key=lambda b: b[0], reverse=True) # RTL
                for item in line:
                    final_text_parts.append(item[2][1])
                    total_conf += item[2][2]
                    
            version_text = " ".join(final_text_parts)
            version_meta_text = " ".join([m[2][1] for m in meta_boxes])
            version_conf = total_conf / max(1, len(main_boxes))
            
            if version_conf > best_confidence and len(version_text.strip()) > 0:
                best_confidence = version_conf
                best_text = version_text.strip()
                best_meta = version_meta_text.strip()
                
        except Exception as e:
            print("OCR Error:", e)
            continue
    
    if best_text is None: return _empty_result()
    sanitized_text = sanitize_plate_text(best_text, "arabic")
    return parse_plate_text(sanitized_text, best_meta, best_confidence)

def parse_plate_text(raw_text, meta_text, confidence):
    cleaned = raw_text.strip()
    
    # Identify Police vs Private meta-text exclusively from the Top Area
    mt_up = meta_text.upper()
    is_police = any(w in mt_up for w in ["POLICE", "P0LICE", "شرط", "POL1CE", "POUICE"])
    is_private = any(w in mt_up for w in ["EGYPT", "EGY", "مصر", "E6YPT"])
    
    # Auto-fix common optical misreads in Arabic plates
    cleaned = cleaned.replace('.', '٠').replace('-', '٠').replace('_', '٠')
    cleaned = cleaned.replace('O', '٥').replace('o', '٥').replace('0', '٠')
    cleaned = cleaned.replace('1', '١').replace('2', '٢').replace('3', '٣')
    cleaned = cleaned.replace('4', '٤').replace('5', '٥').replace('6', '٦')
    cleaned = cleaned.replace('7', '٧').replace('8', '٨').replace('9', '٩')
    
    digits, letters = [], []
    for char in cleaned:
        if char in ARABIC_TO_WESTERN: digits.append(char)
        elif char.isdigit(): digits.append(WESTERN_TO_ARABIC.get(char, char))
        elif char in VALID_PLATE_LETTERS or _is_arabic_letter(char): letters.append(char)
    
    # PaddleOCR reads spaced Arabic letters LTR. Reversing the array restores proper RTL rendering.
    letters.reverse()
    
    numbers_str = " ".join(digits) if digits else ""
    letters_str = " ".join(letters) if letters else ""
    full_text = f"{letters_str} {numbers_str}".strip()
    return {
        "full_text": full_text, "letters": letters_str, "numbers": numbers_str,
        "letters_list": letters, "digits_list": digits, "num_letters": len(letters),
        "num_digits": len(digits), "confidence": round(confidence, 4), "raw_text": raw_text,
        "is_police": is_police, "is_private": is_private
    }

def _is_arabic_letter(char): return (0x0621 <= ord(char) <= 0x064A) or (0x0671 <= ord(char) <= 0x06D3)
def _empty_result(): return {"full_text": "", "letters": "", "numbers": "", "letters_list": [], "digits_list": [], "num_letters": 0, "num_digits": 0, "confidence": 0.0, "raw_text": "", "is_police": False, "is_private": False}
