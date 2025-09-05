#!/usr/bin/env python3
"""
Script to replace all manifest icons with new ones from source image
Usage: python3 scrpit.py "GOLD EDU 3-03.png"
"""

import os
import sys
import re
from PIL import Image, ImageOps

def parse_size_from_filename(filename):
    """Extract width and height from filename"""
    # For apple-splash-1125-2436.jpg -> (1125, 2436)
    if filename.startswith('apple-splash-'):
        match = re.search(r'apple-splash-(\d+)-(\d+)\.(jpg|png)', filename)
        if match:
            return (int(match.group(1)), int(match.group(2)))
    
    # For apple-icon-180.png -> (180, 180)
    elif filename.startswith('apple-icon-'):
        match = re.search(r'apple-icon-(\d+)\.(png|jpg)', filename)
        if match:
            size = int(match.group(1))
            return (size, size)
    
    # For manifest-icon-192.maskable.png -> (192, 192)
    elif filename.startswith('manifest-icon-'):
        match = re.search(r'manifest-icon-(\d+)\.maskable\.(png|jpg)', filename)
        if match:
            size = int(match.group(1))
            return (size, size)
    
    return None

def create_splash_screen(logo, size, background_color='#ffffff'):
    """Create splash screen with centered logo"""
    width, height = size
    
    # Create background
    splash = Image.new('RGB', size, background_color)
    
    # Calculate logo size (15% of smaller dimension)
    logo_size = min(width, height) // 7
    logo_resized = ImageOps.fit(logo, (logo_size, logo_size), Image.Resampling.LANCZOS)
    
    # Center the logo
    x = (width - logo_size) // 2
    y = (height - logo_size) // 2
    
    # Paste logo (handle transparency)
    if logo_resized.mode in ('RGBA', 'LA'):
        splash.paste(logo_resized, (x, y), logo_resized)
    else:
        splash.paste(logo_resized, (x, y))
    
    return splash

def create_icon(logo, size):
    """Create icon with proper sizing"""
    return ImageOps.fit(logo, size, Image.Resampling.LANCZOS)

def replace_manifest_files(source_image_path):
    """Replace all files in manifest directory"""
    
    manifest_dir = "./manifest"
    
    if not os.path.exists(source_image_path):
        print(f"❌ Source image not found: {source_image_path}")
        return False
    
    if not os.path.exists(manifest_dir):
        print(f"❌ Manifest directory not found: {manifest_dir}")
        return False
    
    try:
        # Load source image
        with Image.open(source_image_path) as source:
            print(f"🖼️  Source image: {source_image_path} ({source.size[0]}x{source.size[1]})")
            
            # Get all files in manifest directory
            files = os.listdir(manifest_dir)
            processed = 0
            
            print(f"\n🔄 Processing {len(files)} files...")
            
            for filename in files:
                file_path = os.path.join(manifest_dir, filename)
                
                # Skip if not a file
                if not os.path.isfile(file_path):
                    continue
                
                # Parse size from filename
                size = parse_size_from_filename(filename)
                if not size:
                    print(f"  ⚠️  Skipped {filename} (couldn't parse size)")
                    continue
                
                try:
                    # Create appropriate image based on file type
                    if filename.startswith('apple-splash-'):
                        # Splash screen
                        new_image = create_splash_screen(source, size)
                        new_image.save(file_path, 'JPEG', quality=85, optimize=True)
                    else:
                        # Icon
                        new_image = create_icon(source, size)
                        new_image.save(file_path, 'PNG', optimize=True)
                    
                    print(f"  ✅ {filename} ({size[0]}x{size[1]})")
                    processed += 1
                    
                except Exception as e:
                    print(f"  ❌ Failed {filename}: {e}")
            
            print(f"\n🎉 Successfully processed {processed}/{len(files)} files!")
            return True
            
    except Exception as e:
        print(f"❌ Error loading source image: {e}")
        return False

def main():
    print("🚀 Manifest Icon Replacer")
    
    # Look for source images in current directory
    possible_sources = [
        "GOLD EDU 3-03.png",
        "GOLD EDU 3-04.png"
    ]
    
    source_image = None
    
    # Use command line argument if provided
    if len(sys.argv) > 1:
        source_image = sys.argv[1]
    else:
        # Auto-detect source image
        for img in possible_sources:
            if os.path.exists(img):
                source_image = img
                break
    
    if not source_image:
        print("❌ No source image found!")
        print("Available images:")
        for f in os.listdir('.'):
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                print(f"  - {f}")
        print("\nUsage: python3 scrpit.py <image_file>")
        return
    
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🎯 Source image: {source_image}")
    
    if replace_manifest_files(source_image):
        print("\n✅ All manifest files updated successfully!")
        print("💡 You may need to rebuild your app to see changes.")
    else:
        print("\n❌ Failed to update manifest files.")

if __name__ == "__main__":
    main()