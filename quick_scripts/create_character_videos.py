#!/usr/bin/env python3
"""
Character Animation Video Generator
Creates 100-second MP4 videos of animated Peter and Stewie characters
"""

import subprocess
from pathlib import Path
import time

# Paths
ASSETS = Path("assets")
OUTPUT_DIR = ASSETS / "character_videos"
CHARACTERS = {
    "Peter": {"image": ASSETS / "images/Peter.png", "size": "200:200"},
    "Stewie": {"image": ASSETS / "images/Stewie.png", "size": "180:180"}
}

# Video settings
WIDTH, HEIGHT = 1080, 1920
DURATION = 100  # 100 seconds
FPS = 30

def check_hardware_acceleration():
    """Check if VideoToolbox hardware acceleration is available"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-encoders'],
            capture_output=True, text=True, check=True
        )
        return 'h264_videotoolbox' in result.stdout
    except:
        return False

def get_encoder_settings():
    """Get optimal encoder settings based on hardware availability"""
    if check_hardware_acceleration():
        print("🚀 Apple Silicon VideoToolbox acceleration detected")
        return {
            'hwaccel': ['-hwaccel', 'videotoolbox'],
            'video_codec': 'h264_videotoolbox',
            'quality_settings': ['-b:v', '8M']
        }
    else:
        print("🔧 Using software encoding (libx264)")
        return {
            'hwaccel': [],
            'video_codec': 'libx264',
            'quality_settings': ['-crf', '18', '-preset', 'medium']
        }

def create_character_video(character_name, character_data, output_dir):
    """Create animated character video"""
    print(f"\n🎭 Creating {character_name} animation video...")
    
    image_path = character_data["image"]
    size = character_data["size"]
    output_path = output_dir / f"{character_name.lower()}_animated.mp4"
    
    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        return False
    
    # Character-specific rotation (opposite directions) - 5x more dramatic
    if character_name == "Peter":
        rotation = "0.435*sin(2*PI/2*t)"  # Clockwise tilt (5x stronger)
    else:  # Stewie
        rotation = "-0.435*sin(2*PI/2*t)"  # Counter-clockwise tilt (5x stronger)
    
    # Create green screen background
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f'color=c=green:size={WIDTH}x{HEIGHT}:duration={DURATION}:rate={FPS}',
        '-loop', '1', '-i', str(image_path),
        '-filter_complex', 
        f'[1:v]scale={size}[scaled];'
        f'[scaled]rotate={rotation}:ow=rotw(iw):oh=roth(ih):c=green[rotated];'
        f'[0:v][rotated]overlay=x=(W-w)/2:y=(H-h)/2:shortest=1[final]',
        '-map', '[final]',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '18',
        '-preset', 'medium',
        '-t', str(DURATION),
        str(output_path)
    ]
    
    try:
        print(f"  📹 Rendering {character_name} animation ({DURATION}s @ {FPS}fps)...")
        start_time = time.time()
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        render_time = time.time() - start_time
        print(f"  ✅ {character_name} video created: {output_path}")
        print(f"  ⏱️  Render time: {render_time:.1f} seconds")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to create {character_name} video")
        print(f"  Command: {' '.join(e.cmd)}")
        print(f"  Error: {e.stderr}")
        return False

def create_positioned_character_videos():
    """Create character videos pre-positioned for final composition"""
    print("\n🎬 Creating positioned character videos...")
    
    output_dir = OUTPUT_DIR / "positioned"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for character_name, character_data in CHARACTERS.items():
        print(f"\n🎭 Creating positioned {character_name} video...")
        
        image_path = character_data["image"]
        size = character_data["size"]
        
        if not image_path.exists():
            print(f"❌ Image not found: {image_path}")
            continue
        
        # Position characters with actual pixel values
        if character_name == "Peter":
            x_pos, y_pos = 50, HEIGHT - 250  # Bottom left (50px from left, 250px from bottom)
            rotation = "0.435*sin(2*PI/2*t)"  # 5x stronger rocking
        else:  # Stewie
            x_pos, y_pos = WIDTH - 230, HEIGHT - 230  # Bottom right (230px from right edge, 230px from bottom)
            rotation = "-0.435*sin(2*PI/2*t)"  # 5x stronger rocking
        
        output_path = output_dir / f"{character_name.lower()}_positioned.mp4"
        
        # Create positioned character video with green screen
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', f'color=c=green:size={WIDTH}x{HEIGHT}:duration={DURATION}:rate={FPS}',
            '-loop', '1', '-i', str(image_path),
            '-filter_complex', 
            f'[1:v]scale={size}[scaled];'
            f'[scaled]rotate={rotation}:ow=rotw(iw):oh=roth(ih):c=green[rotated];'
            f'[0:v][rotated]overlay=x={x_pos}:y={y_pos}:shortest=1[final]',
            '-map', '[final]',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '18',
            '-preset', 'medium',
            '-t', str(DURATION),
            str(output_path)
        ]
        
        try:
            print(f"  📹 Rendering positioned {character_name}...")
            start_time = time.time()
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            render_time = time.time() - start_time
            print(f"  ✅ Positioned {character_name} video: {output_path}")
            print(f"  ⏱️  Render time: {render_time:.1f} seconds")
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to create positioned {character_name} video")
            print(f"  Command: {' '.join(e.cmd)}")
            print(f"  Error: {e.stderr}")

def main():
    """Main function to create character videos"""
    print("=" * 60)
    print("CHARACTER ANIMATION VIDEO GENERATOR")
    print("=" * 60)
    print(f"🎯 Creating {DURATION}-second character animations")
    print(f"📐 Video size: {WIDTH}x{HEIGHT} @ {FPS}fps")
    
    # Create output directory
    print(f"\n📁 Creating output directory: {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ Output directory created/exists")
    
    # Check images exist
    print("\n🔍 Checking character images...")
    missing_images = False
    for name, data in CHARACTERS.items():
        if data["image"].exists():
            print(f"  ✅ {name}: {data['image']}")
        else:
            print(f"  ❌ {name}: {data['image']} (missing)")
            missing_images = True
    
    if missing_images:
        print("❌ Missing character images. Exiting.")
        return False
    
    # Create individual character videos
    print(f"\n🎬 Creating individual character videos...")
    success_count = 0
    for character_name, character_data in CHARACTERS.items():
        if create_character_video(character_name, character_data, OUTPUT_DIR):
            success_count += 1
    
    # Create positioned character videos
    create_positioned_character_videos()
    
    print(f"\n🎉 Character video creation complete!")
    print(f"📊 Success: {success_count}/{len(CHARACTERS)} individual videos")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print("=" * 60)
    
    # List created files
    print("\n📋 Created files:")
    for file in sorted(OUTPUT_DIR.rglob("*.mp4")):
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  📹 {file.relative_to(OUTPUT_DIR)}: {size_mb:.1f} MB")
    
    return True

if __name__ == "__main__":
    main()
