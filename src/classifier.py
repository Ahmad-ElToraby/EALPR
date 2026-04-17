import re

PREFIX_DICT = {
    "CA": "Qena",
    "CK": "Luxor",
    "CW": "Aswan",
    "TD": "Damietta",
    "TE": "Port Said",
    "TC": "Ismailia",
    "TS": "Suez",
    "TR": "Red Sea",
    "TA": "North Sinai",
    "TG": "South Sinai",
    "GH": "Matrouh",
    "GB": "New Valley",
}

SUFFIX_DICT = {
    "S": "Alexandria",
    "K": "Qalyubia",
    "R": "Sharqia",
    "M": "Monufia",
    "B": "Beheira",
    "D": "Dakahlia",
    "E": "Gharbia",
    "L": "Kafr El Sheikh",
    "F": "Faiyum",
    "W": "Beni Suef",
    "N": "Minya",
    "Y": "Asyut",
    "H": "Sohag",
}

def classify_governorate(plate: str) -> str:
    """Classifies the governorate based on plate string."""
    # STEP 1
    cleaned = re.sub(r'[\s\-_]', '', plate).upper()
    digits = [c for c in cleaned if c.isdigit()]
    letters = [c for c in cleaned if c.isalpha()]
    
    digit_count = len(digits)
    letter_count = len(letters)
    
    # STEP 2
    if digit_count == 3:
        return "Cairo"
        
    # STEP 3
    if letter_count == 2:
        return "Giza"
        
    # STEP 4
    letters_str = "".join(letters)
    if len(letters_str) >= 3:
        first_two = letters_str[:2]
        if first_two in PREFIX_DICT:
            return PREFIX_DICT[first_two]
            
        # STEP 5
        last_letter = letters_str[-1]
        if last_letter in SUFFIX_DICT:
            return SUFFIX_DICT[last_letter]
            
    # STEP 6
    return "Unknown"

def main():
    test_cases = [
        # Cairo cases (3 digits)
        ("123-ABC", "Cairo"),
        ("567-ABG", "Cairo"),
        
        # Giza cases (2 letters)
        ("1234-AB", "Giza"),
        ("8888-ZX", "Giza"),
        
        # Prefix cases (First two letters match prefix dictionary)
        ("4521-TSA", "Suez"), # TS = Suez
        ("9012-TEA", "Port Said"), # TE = Port Said
        
        # Suffix cases (Last letter matches suffix dictionary)
        ("1234-NMS", "Alexandria"), # S = Alexandria
        ("4521-NDK", "Qalyubia"), # K = Qalyubia
        
        # Unknown cases
        ("9999-XYZ", "Unknown"),
        ("1111-QQQ", "Unknown")
    ]
    
    passed = 0
    print("Running Tests:")
    print("-" * 30)
    for plate, expected in test_cases:
        result = classify_governorate(plate)
        if result == expected:
            print(f"PASS: {plate} -> {result}")
            passed += 1
        else:
            print(f"FAIL: {plate} -> expected '{expected}', got '{result}'")
            
    print("-" * 30)
    print(f"Passed {passed}/{len(test_cases)} tests.")

if __name__ == "__main__":
    main()
