#!/usr/bin/env python3
"""
YouTube Video Downloader
Downloads YouTube videos in the highest available quality.
"""

import os
import sys
import argparse
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("yt-dlp is not installed. Installing it now...")
    os.system("pip install yt-dlp")
    import yt_dlp


def download_video(url, output_path="./downloads"):
    """Download a YouTube video in the highest quality available."""
    
    # Create output directory if it doesn't exist
    Path(output_path).mkdir(exist_ok=True)
    
    # yt-dlp options for highest quality (targeting 1440p60)
    ydl_opts = {
        'format': 'bestvideo[height<=1440][fps<=60][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440]/best',
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'merge_output_format': 'mp4',
        'writeinfojson': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading: {url}")
            ydl.download([url])
            print("Download completed successfully!")
            
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return False
    
    return True


def quick_download(url):
    """Quick download function - just provide a URL and it downloads to current directory."""
    return download_video(url, "./")


def main():
    parser = argparse.ArgumentParser(description="Download YouTube videos in highest quality")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("-o", "--output", default="./downloads", 
                       help="Output directory (default: ./downloads)")
    
    args = parser.parse_args()
    
    if not args.url:
        print("Please provide a YouTube URL")
        sys.exit(1)
    
    success = download_video(args.url, args.output)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=u7kdVe8q5zs"
    quick_download(url)