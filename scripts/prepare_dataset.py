"""
Dataset Preparation Script for EALPR
- Reads images from Vehicles/ and labels from Vehicles Labeling/
- Normalizes images to 640x640
- Applies augmentation (rotation, brightness, noise, blur)
- Splits into train/val/test (70/15/15)
"""
import os
import sys
import shutil
import random
import cv2
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
import albumentations as A

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "Vehicles"
LABELS_DIR = BASE_DIR / "Vehicles Labeling"
OUTPUT_DIR = BASE_DIR / "dataset"
IMG_SIZE = 640

def get_image_label_pairs():
    """Get matched image-label pairs."""
    pairs = []
    for img_file in sorted(IMAGES_DIR.iterdir()):
        if img_file.suffix.lower() in ('.jpg', '.jpeg', '.png'):
            label_file = LABELS_DIR / (img_file.stem + '.txt')
            if label_file.exists() and label_file.name != 'classes.txt':
                pairs.append((img_file, label_file))
    print(f"Found {len(pairs)} image-label pairs")
    return pairs

def create_augmentation_pipeline():
    """Create augmentation pipeline with bbox support."""
    return A.Compose([
        A.Rotate(limit=15, border_mode=cv2.BORDER_CONSTANT, p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.5),
        A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
        A.OneOf([
            A.MotionBlur(blur_limit=5, p=1.0),
            A.GaussianBlur(blur_limit=(3, 5), p=1.0),
        ], p=0.3),
        A.CLAHE(clip_limit=2.0, p=0.2),
        A.RandomGamma(gamma_limit=(80, 120), p=0.2),
    ], bbox_params=A.BboxParams(
        format='yolo',
        label_fields=['class_labels'],
        min_visibility=0.3
    ))

def read_yolo_labels(label_path):
    """Read YOLO format labels."""
    bboxes = []
    class_labels = []
    with open(label_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split()
                cls = int(parts[0])
                x_center, y_center, width, height = map(float, parts[1:5])
                bboxes.append([x_center, y_center, width, height])
                class_labels.append(cls)
    return bboxes, class_labels

def write_yolo_labels(label_path, bboxes, class_labels):
    """Write YOLO format labels."""
    with open(label_path, 'w') as f:
        for bbox, cls in zip(bboxes, class_labels):
            x_center, y_center, width, height = bbox
            f.write(f"{cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

def process_image(img_path, label_path, output_img_dir, output_label_dir, 
                  augment_pipeline=None, prefix=""):
    """Process a single image: resize and optionally augment."""
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"Warning: Could not read {img_path}")
        return 0
    
    bboxes, class_labels = read_yolo_labels(label_path)
    if not bboxes:
        return 0
    
    # Resize to IMG_SIZE x IMG_SIZE
    img_resized = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    
    # Save original resized image
    stem = prefix + img_path.stem
    out_img_path = output_img_dir / f"{stem}.jpg"
    out_label_path = output_label_dir / f"{stem}.txt"
    
    cv2.imwrite(str(out_img_path), img_resized)
    write_yolo_labels(out_label_path, bboxes, class_labels)
    count = 1
    
    # Apply augmentation if pipeline provided
    if augment_pipeline is not None:
        try:
            # Clamp bboxes to valid YOLO range
            valid_bboxes = []
            valid_labels = []
            for bbox, cls in zip(bboxes, class_labels):
                x_c, y_c, w, h = bbox
                x_c = max(0.001, min(0.999, x_c))
                y_c = max(0.001, min(0.999, y_c))
                w = max(0.001, min(1.0, w))
                h = max(0.001, min(1.0, h))
                if (x_c - w/2) >= 0 and (x_c + w/2) <= 1 and \
                   (y_c - h/2) >= 0 and (y_c + h/2) <= 1:
                    valid_bboxes.append([x_c, y_c, w, h])
                    valid_labels.append(cls)
            
            if valid_bboxes:
                augmented = augment_pipeline(
                    image=img_resized,
                    bboxes=valid_bboxes,
                    class_labels=valid_labels
                )
                
                if augmented['bboxes']:
                    aug_img_path = output_img_dir / f"{stem}_aug.jpg"
                    aug_label_path = output_label_dir / f"{stem}_aug.txt"
                    cv2.imwrite(str(aug_img_path), augmented['image'])
                    write_yolo_labels(aug_label_path, 
                                     augmented['bboxes'], 
                                     augmented['class_labels'])
                    count += 1
        except Exception:
            pass  # Skip failed augmentations silently
    
    return count

def main():
    print("=" * 60)
    print("EALPR Dataset Preparation")
    print("=" * 60)
    
    pairs = get_image_label_pairs()
    if not pairs:
        print("ERROR: No image-label pairs found!")
        sys.exit(1)
    
    random.seed(42)
    train_pairs, temp_pairs = train_test_split(pairs, test_size=0.30, random_state=42)
    val_pairs, test_pairs = train_test_split(temp_pairs, test_size=0.50, random_state=42)
    
    print(f"\nDataset split:")
    print(f"  Train: {len(train_pairs)} images")
    print(f"  Val:   {len(val_pairs)} images")
    print(f"  Test:  {len(test_pairs)} images")
    
    splits = {'train': train_pairs, 'val': val_pairs, 'test': test_pairs}
    if OUTPUT_DIR.exists(): shutil.rmtree(OUTPUT_DIR)
    
    aug_pipeline = create_augmentation_pipeline()
    total_images = 0
    
    for split_name, split_pairs in splits.items():
        img_dir = OUTPUT_DIR / split_name / "images"
        label_dir = OUTPUT_DIR / split_name / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        
        split_count = 0
        for i, (img_path, label_path) in enumerate(split_pairs):
            pipeline = aug_pipeline if split_name == 'train' else None
            count = process_image(img_path, label_path, img_dir, label_dir, pipeline)
            split_count += count
            if (i + 1) % 100 == 0:
                print(f"  [{split_name}] Processed {i + 1}/{len(split_pairs)}...")
        
        total_images += split_count
        print(f"  [{split_name}] Total: {split_count} images (with augmentation)")
    
    data_yaml = OUTPUT_DIR / "data.yaml"
    abs_dataset_path = str(OUTPUT_DIR.resolve()).replace('\\', '/')
    with open(data_yaml, 'w') as f:
        f.write(f"path: {abs_dataset_path}\n")
        f.write("train: train/images\n")
        f.write("val: val/images\n")
        f.write("test: test/images\n")
        f.write("nc: 1\n")
        f.write("names: ['License Plate']\n")
    
    print(f"\nDataset preparation complete! Cost: {total_images} images")

if __name__ == "__main__":
    main()
