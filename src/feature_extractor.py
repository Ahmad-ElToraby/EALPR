"""
Feature Extractor for Egyptian License Plates
"""
import cv2
import numpy as np

# color name, lower HSV, upper HSV, English type, Arabic type
PLATE_COLOR_RANGES = [
    ("light_blue", np.array([85, 40, 80]), np.array([110, 255, 255]), "Private", "ملاكي"),
    ("orange", np.array([5, 100, 80]), np.array([30, 255, 255]), "Taxi", "تاكسي"),
    ("red", np.array([0, 80, 80]), np.array([5, 255, 255]), "Truck/Commercial", "نقل"),
    ("red", np.array([170, 80, 80]), np.array([180, 255, 255]), "Truck/Commercial", "نقل"),
    ("dark_blue", np.array([110, 40, 30]), np.array([140, 255, 255]), "Police", "شرطة"),
    ("green", np.array([35, 50, 50]), np.array([85, 255, 255]), "Diplomatic", "دبلوماسي"),
    ("yellow", np.array([20, 80, 80]), np.array([35, 255, 255]), "Temporary/Customs", "مؤقت"),
    ("gray", np.array([0, 0, 80]), np.array([180, 40, 180]), "Public Bus", "نقل عام"),
    ("beige", np.array([15, 20, 150]), np.array([30, 80, 240]), "Limousine/Tourist", "ليموزين"),
]
DEFAULT_COLOR = ("white", "Private", "ملاكي")

def detect_plate_color(plate_img):
    if plate_img is None or plate_img.size == 0:
        return {"color": DEFAULT_COLOR[0], "vehicle_type": DEFAULT_COLOR[1], "vehicle_type_ar": DEFAULT_COLOR[2], "confidence": 0.0}
    
    h, w = plate_img.shape[:2]
    strip_height = max(1, int(h * 0.35))
    top_strip = plate_img[0:strip_height, :]
    if len(top_strip.shape) == 2: top_strip = cv2.cvtColor(top_strip, cv2.COLOR_GRAY2BGR)
    
    pixels = top_strip.reshape((-1, 3))
    pixels = np.float32(pixels)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    try:
        _, labels, centers = cv2.kmeans(pixels, 3, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        centers = np.uint8(centers)
        hsv_centers = cv2.cvtColor(centers.reshape(3, 1, 3), cv2.COLOR_BGR2HSV).reshape(3, 3)
        
        counts = np.bincount(labels.flatten())
        sorted_indices = np.argsort(counts)[::-1]
        
        for c_idx in sorted_indices:
            dom_h, dom_s, dom_v = hsv_centers[c_idx]
            if dom_s < 30 or dom_v < 30: continue # Skip bounds
            
            for cname, low, up, vt_en, vt_ar in PLATE_COLOR_RANGES:
                if (low[0] <= dom_h <= up[0] or (up[0] < low[0] and (dom_h >= low[0] or dom_h <= up[0]))) and \
                   low[1] <= dom_s <= up[1] and low[2] <= dom_v <= up[2]:
                    return {"color": cname, "vehicle_type": vt_en, "vehicle_type_ar": vt_ar, "confidence": round(float(counts[c_idx]/len(pixels)), 4)}
    except Exception as e: print(e)
    return {"color": DEFAULT_COLOR[0], "vehicle_type": DEFAULT_COLOR[1], "vehicle_type_ar": DEFAULT_COLOR[2], "confidence": 0.5}

def detect_layout(plate_img):
    if plate_img is None or plate_img.size == 0: return "unknown"
    h, w = plate_img.shape[:2]
    aspect_ratio = w / h if h > 0 else 0
    return "horizontal" if aspect_ratio > 2.5 else "stacked" if aspect_ratio < 2.0 else "standard"

def extract_features(plate_img):
    color = detect_plate_color(plate_img)
    return {
        "plate_color": color["color"], "vehicle_type": color["vehicle_type"], 
        "vehicle_type_ar": color["vehicle_type_ar"], "color_confidence": color["confidence"], "layout": detect_layout(plate_img)
    }
