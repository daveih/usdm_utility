#!/usr/bin/env python3
"""
Image Renamer - Renames image files based on metadata timestamps
Renames files to format: YYYY-MM-DD_<index>.<ext>
where <index> is chronological order within the day
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
from collections import defaultdict
import argparse


def get_image_datetime(image_path):
    """
    Extract datetime from image EXIF metadata.
    Returns datetime object or None if not available.
    """
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        
        if exif_data is None:
            return None
        
        # Look for DateTimeOriginal (when photo was taken)
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'DateTimeOriginal' or tag == 'DateTime':
                # EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
                dt = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                return dt
        
        return None
    except Exception as e:
        print(f"Warning: Could not read EXIF data from {image_path}: {e}")
        return None


def get_file_modification_time(file_path):
    """
    Get file modification time as fallback.
    """
    try:
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp)
    except Exception as e:
        print(f"Warning: Could not get modification time for {file_path}: {e}")
        return None


def get_image_files(directory):
    """
    Get all jpg and png files in the directory.
    """
    directory = Path(directory)
    image_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    
    image_files = []
    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix in image_extensions:
            image_files.append(file_path)
    
    return image_files


def rename_images(directory, dry_run=False):
    """
    Rename all images in directory based on metadata timestamps.
    
    Args:
        directory: Path to directory containing images
        dry_run: If True, only print what would be done without renaming
    """
    directory = Path(directory)
    
    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist")
        return
    
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory")
        return
    
    # Get all image files
    image_files = get_image_files(directory)
    
    if not image_files:
        print(f"No image files (jpg/png) found in '{directory}'")
        return
    
    print(f"Found {len(image_files)} image file(s)")
    
    # Extract timestamps for each image
    images_with_times = []
    for image_path in image_files:
        dt = get_image_datetime(image_path)
        
        # Fallback to file modification time if no EXIF data
        if dt is None:
            dt = get_file_modification_time(image_path)
        
        if dt is None:
            print(f"Warning: Skipping {image_path.name} - no timestamp available")
            continue
        
        images_with_times.append((image_path, dt))
    
    if not images_with_times:
        print("No images with valid timestamps found")
        return
    
    # Sort by datetime
    images_with_times.sort(key=lambda x: x[1])
    
    # Group by date and assign indices
    images_by_date = defaultdict(list)
    for image_path, dt in images_with_times:
        date_str = dt.strftime('%Y-%m-%d')
        images_by_date[date_str].append((image_path, dt))
    
    # Rename files
    renamed_count = 0
    skipped_count = 0
    
    for date_str, images in sorted(images_by_date.items()):
        # Sort images within the same day by time
        images.sort(key=lambda x: x[1])
        
        for index, (image_path, dt) in enumerate(images, start=1):
            original_name = image_path.name
            extension = image_path.suffix
            new_name = f"{date_str}_{index}{extension}"
            new_path = image_path.parent / new_name
            
            # Check if file already has correct name
            if image_path.name == new_name:
                print(f"Skipped: {original_name} (already correctly named)")
                skipped_count += 1
                continue
            
            # Check if target filename already exists
            if new_path.exists() and new_path != image_path:
                print(f"Warning: Target {new_name} already exists, skipping {original_name}")
                skipped_count += 1
                continue
            
            if dry_run:
                print(f"Would rename: {original_name} -> {new_name} ({dt})")
            else:
                try:
                    image_path.rename(new_path)
                    print(f"Renamed: {original_name} -> {new_name} ({dt})")
                    renamed_count += 1
                except Exception as e:
                    print(f"Error renaming {original_name}: {e}")
                    skipped_count += 1
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:")
    print(f"  Renamed: {renamed_count}")
    print(f"  Skipped: {skipped_count}")


def main():
    parser = argparse.ArgumentParser(
        description='Rename image files based on metadata timestamps',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rename_images.py /path/to/images
  python rename_images.py /path/to/images --dry-run
  python rename_images.py .

Output format: YYYY-MM-DD_<index>.<ext>
where <index> is chronological order within the day
        """
    )
    
    parser.add_argument(
        'directory',
        help='Directory containing image files to rename'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be renamed without actually renaming files'
    )
    
    args = parser.parse_args()
    
    rename_images(args.directory, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
