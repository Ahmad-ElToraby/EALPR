"""
Import this in main.py and expose GET /config to give the frontend all labels, colors, and categories in one call.
"""

SEVERITY_MAP = {
    1: {
        "level": 1,
        "label_en": "Low",
        "label_ar": "منخفض",
        "color_hex": "#FFC107",
        "color_name": "amber",
        "icon": "⚠️",
        "description_en": "Mildly suspicious behavior, no confirmed threat",
        "description_ar": "سلوك مريب بشكل طفيف، لا يوجد تهديد مؤكد"
    },
    2: {
        "level": 2,
        "label_en": "Medium",
        "label_ar": "متوسط",
        "color_hex": "#FF9800",
        "color_name": "orange",
        "icon": "🔶",
        "description_en": "Repeated suspicious activity or minor violation",
        "description_ar": "نشاط مريب متكرر أو مخالفة بسيطة"
    },
    3: {
        "level": 3,
        "label_en": "High",
        "label_ar": "مرتفع",
        "color_hex": "#F44336",
        "color_name": "red",
        "icon": "🚨",
        "description_en": "Dangerous driving or confirmed threat to safety",
        "description_ar": "قيادة خطرة أو تهديد مؤكد للسلامة"
    },
    4: {
        "level": 4,
        "label_en": "Critical",
        "label_ar": "حرج",
        "color_hex": "#7B1FA2",
        "color_name": "purple",
        "icon": "🚫",
        "description_en": "Stolen vehicle, wanted plate, or active criminal threat",
        "description_ar": "مركبة مسروقة أو لوحة مطلوبة أو تهديد جنائي نشط"
    }
}

CATEGORY_LIST = [
    "Suspicious",
    "Reckless Driving", 
    "Stolen Vehicle",
    "Expired Tripticket",
    "Wrong Zone - Commercial",
    "Harassment",
    "Speeding",
    "Drives Under the Influence",
    "Aggressive / Road Rage",
    "Rude Behavior / Uncooperative",
    "Loud Music",
    "Poor Vehicle Hygiene",
    "Low Quality / Unsafe Vehicle",
    "Dropped in Wrong Location",
    "Asked for More Money / Greedy",
    "Poor Service",
    "Other"
]

SEVERITY_THRESHOLDS = {
    1: 1,   # Low — 1 report
    2: 3,   # Medium — 3 or more reports  
    3: 7,   # High — 7 or more reports
    4: 15   # Critical — 15 or more reports
}

def calculate_severity(report_count: int) -> int:
    """
    Returns the appropriate severity level (1-4) based on SEVERITY_THRESHOLDS.
    Logic: find the highest threshold that report_count meets or exceeds.
    """
    severity = 1
    for level, threshold in sorted(SEVERITY_THRESHOLDS.items()):
        if report_count >= threshold:
            severity = level
    return severity

def get_severity_info(level: int) -> dict:
    """
    Returns the severity dict for a given level.
    Raises ValueError if level not in 1-4.
    """
    if level not in SEVERITY_MAP:
        raise ValueError(f"Severity level {level} is invalid. Must be between 1 and 4.")
    return SEVERITY_MAP[level]

def get_all_severities() -> list:
    """
    Returns list of all four severity dicts ordered by level.
    """
    return [SEVERITY_MAP[level] for level in sorted(SEVERITY_MAP.keys())]

def get_categories() -> list:
    """
    Returns CATEGORY_LIST.
    """
    return CATEGORY_LIST

if __name__ == "__main__":
    import json
    print("Severity Configuration:")
    print(json.dumps(get_all_severities(), ensure_ascii=False, indent=2))
    print("\nAvailable Categories:")
    print(json.dumps(get_categories(), ensure_ascii=False, indent=2))
