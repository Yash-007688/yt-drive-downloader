import yt_dlp
import sys
import urllib.request
import urllib.parse
import re
import argparse
import os
import subprocess
from typing import List, Optional, Tuple
from pytube import YouTube
from youtube_comment_downloader import YoutubeCommentDownloader
import gdown
from dotenv import load_dotenv, set_key

sys.stdout.reconfigure(encoding='utf-8')

DRIVE_FILE_PATTERNS = [
    r"https?://drive\.google\.com/file/d/([a-zA-Z0-9_-]{10,})",
    r"https?://drive\.google\.com/open\?id=([a-zA-Z0-9_-]{10,})",
    r"https?://drive\.google\.com/uc\?id=([a-zA-Z0-9_-]{10,})",
]

DRIVE_FOLDER_PATTERNS = [
    r"https?://drive\.google\.com/drive/folders/([a-zA-Z0-9_-]{10,})",
    r"https?://drive\.google\.com/drive/u/\d/folders/([a-zA-Z0-9_-]{10,})",
]

DRIVE_URL_REGEX = re.compile(
    r"https?://drive\.google\.com/(?:file/d/[a-zA-Z0-9_-]{10,}|open\?id=[a-zA-Z0-9_-]{10,}|uc\?id=[a-zA-Z0-9_-]{10,}|drive/(?:u/\d/)?folders/[a-zA-Z0-9_-]{10,})"
)

ENV_FILE = ".env"
DEFAULT_OUTPUT_DIR = "downloads"

def fetch_description(video_url: str, timeout: int = 20) -> str:
    # First try pytube
    try:
        yt = YouTube(video_url)
        desc = yt.description or ""
        if desc:
            return desc
    except Exception:
        pass

    # Fallback to yt-dlp if available
    if yt_dlp is not None:
        ydl_opts = {
            "quiet": True,
            "noplaylist": True,
            "skip_download": True,
            "nocheckcertificate": True,
            "extract_flat": "in_playlist",
            "socket_timeout": timeout,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                desc = info.get("description") if isinstance(info, dict) else None
                if isinstance(desc, str):
                    return desc
        except Exception:
            pass

    return ""

def fetch_comments(video_url: str, max_comments: int = 200, timeout: int = 20) -> List[str]:
    downloader = YoutubeCommentDownloader()
    generator = downloader.get_comments_from_url(video_url, sort_by=0)  # 0 = TOP_COMMENTS
    comments: List[str] = []
    for idx, comment in enumerate(generator):
        if idx >= max_comments:
            break
        text = comment.get("text", "")
        if text:
            comments.append(text)
    return comments

def extract_drive_links_from_text(text: str) -> List[str]:
    return list(dict.fromkeys(DRIVE_URL_REGEX.findall(text)))

def extract_all_drive_links(texts) -> List[str]:
    seen = set()
    results: List[str] = []
    for text in texts:
        for url in extract_drive_links_from_text(text):
            if url not in seen:
                seen.add(url)
                results.append(url)
    return results

def classify_drive_url(url: str) -> Tuple[str, Optional[str]]:
    for pattern in DRIVE_FILE_PATTERNS:
        m = re.match(pattern, url)
        if m:
            return ("file", m.group(1))
    for pattern in DRIVE_FOLDER_PATTERNS:
        m = re.match(pattern, url)
        if m:
            return ("folder", m.group(1))
    return ("unknown", None)

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def finalize_part_files(output_dir: str) -> None:
    try:
        for name in os.listdir(output_dir):
            if not name.endswith(".part"):
                continue
            part_path = os.path.join(output_dir, name)
            final_path = os.path.join(output_dir, name[:-5])
            if not os.path.exists(final_path):
                try:
                    os.replace(part_path, final_path)
                except Exception:
                    pass
    except Exception:
        pass

def download_drive_url(url: str, output_dir: str) -> Optional[str]:
    kind, _id = classify_drive_url(url)
    ensure_dir(output_dir)

    if kind == "folder" and _id:
        gdown.download_folder(id=_id, output=output_dir, quiet=False, use_cookies=True, remaining_ok=True)
        finalize_part_files(output_dir)
        return None
    elif kind == "file" and _id:
        path = gdown.download(id=_id, output=output_dir, quiet=False, fuzzy=True, use_cookies=True, resume=True)
        finalize_part_files(output_dir)
        return path
    else:
        path = gdown.download(url, output=output_dir, quiet=False, fuzzy=True, use_cookies=True, resume=True)
        finalize_part_files(output_dir)
        return path

def download_video(url, format='mp4', quality=None, speed=1.0, output_dir='download'):
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
    }
    postprocessors = []
    if format.lower() in ['mp4', 'video']:
        if quality:
            ydl_opts['format'] = f'best[height<={quality}]'
        else:
            ydl_opts['format'] = 'best'
        if speed != 1.0:
            postprocessors.append({
                'key': 'FFmpegVideoConvertor',
                'preferredformat': format,
                'postprocessor_args': ['-filter:v', f'setpts=PTS/{speed}', '-filter:a', f'atempo={speed}'],
            })
    else:
        ydl_opts['format'] = 'bestaudio/best'
        if format.lower() == 'mp3':
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            })
        elif format.lower() == 'wav':
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            })
        if speed != 1.0:
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format.lower(),
                'postprocessor_args': ['-filter:a', f'atempo={speed}'],
            })
    if postprocessors:
        ydl_opts['postprocessors'] = postprocessors
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def fix_videos(output_dir='download'):
    folder = output_dir
    if not os.path.exists(folder):
        print("Download folder does not exist")
        return
    ffmpeg_path = r"C:\Users\YASH\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0-full_build\bin\ffmpeg.exe"
    for file in os.listdir(folder):
        if file.endswith('.mp4'):
            input_path = os.path.join(folder, file)
            temp_path = input_path + '.temp.mp4'
            print(f"Fixing {file}...")
            result = subprocess.run([ffmpeg_path, '-y', '-i', input_path, '-c:v', 'libx264', '-c:a', 'aac', temp_path])
            if result.returncode == 0:
                os.replace(temp_path, input_path)
                print(f"Fixed {file}")
            else:
                print(f"Failed to fix {file}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)

def parse_speed(speed_str):
    if speed_str.endswith('x'):
        return float(speed_str[:-1])
    return float(speed_str)

if __name__ == "__main__":
    load_dotenv(dotenv_path=ENV_FILE, override=False)

    parser = argparse.ArgumentParser(description="Download YouTube videos or playlists and optionally Google Drive links")
    parser.add_argument('-s', '--search', help='Search query for video or playlist')
    parser.add_argument('-l', '--link', help='Direct YouTube URL')
    parser.add_argument('-f', '--format', default='mp4', help='Format: mp3, mp4, wav, etc.')
    parser.add_argument('-q', '--quality', help='Quality: 240, 720, 1080, 4k, etc.')
    parser.add_argument('-u', '--speed', default='1.0', help='Playback speed: 0.5, 1.0, 1.5x, 2.0, etc.')
    parser.add_argument('--output', default=None, help='Output directory (default/env downloads)')
    parser.add_argument('--drive', action='store_true', help='Also scrape and download Google Drive links from the YouTube video')
    parser.add_argument('--max-comments', type=int, default=None, help='Max comments to scan for Drive links (default/env 200)')
    parser.add_argument('--timeout', type=int, default=None, help='Timeout for requests (default/env 20)')
    args = parser.parse_args()

    # Resolve config
    output = args.output or os.getenv("OUTPUT_DIR", DEFAULT_OUTPUT_DIR).strip() or DEFAULT_OUTPUT_DIR
    max_comments = args.max_comments if args.max_comments is not None else int(os.getenv("MAX_COMMENTS", "200"))
    timeout = args.timeout if args.timeout is not None else int(os.getenv("TIMEOUT", "20"))

    if args.format == 'fix':
        fix_videos(output)
        sys.exit(0)

    if args.search:
        query = args.search
        if 'playlist' in query.lower():
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            try:
                with urllib.request.urlopen(search_url) as response:
                    html = response.read().decode('utf-8')
                match = re.search(r'/playlist\?list=([A-Za-z0-9_-]+)', html)
                if match:
                    url = f"https://www.youtube.com/playlist?list={match.group(1)}"
                else:
                    print("No playlist found")
                    sys.exit(1)
            except Exception as e:
                print(f"Error searching: {e}")
                sys.exit(1)
        else:
            url = f"ytsearch:{query}"
    elif args.link:
        url = args.link
        # Auto-save URL to .env
        try:
            if not os.path.exists(ENV_FILE):
                with open(ENV_FILE, "w", encoding="utf-8") as f:
                    f.write("")
            set_key(ENV_FILE, "YOUTUBE_URL", url)
        except Exception:
            pass
    else:
        url = os.getenv("YOUTUBE_URL", "").strip()
        if not url:
            print("Provide -s, -l, or set YOUTUBE_URL in .env")
            parser.print_help()
            sys.exit(1)

    quality_map = {'4k': '2160', '1080p': '1080', '720p': '720', '480p': '480', '360p': '360', '240p': '240'}
    quality = quality_map.get(args.quality.lower(), args.quality) if args.quality else None
    speed = parse_speed(args.speed)
    download_video(url, args.format, quality, speed, output)

    if args.drive:
        # For Drive links, only support single video URLs
        if not args.link and not url.startswith("https://www.youtube.com/watch?v="):
            print("[!] --drive requires a direct YouTube video URL")
            sys.exit(1)
        video_url = args.link or url
        print(f"[+] Fetching description for Drive links: {video_url}")
        description = fetch_description(video_url, timeout)
        print(f"[+] Fetching up to {max_comments} comments")
        comments = fetch_comments(video_url, max_comments, timeout)
        all_texts = [description] + comments
        drive_links = extract_all_drive_links(all_texts)
        if drive_links:
            print(f"[+] Found {len(drive_links)} Google Drive link(s)")
            for link in drive_links:
                print(f"    - {link}")
            for link in drive_links:
                try:
                    download_drive_url(link, output)
                    print(f"[+] Downloaded Drive content from {link}")
                except Exception as e:
                    print(f"[!] Failed to download {link}: {e}")
        else:
            print("[!] No Google Drive links found.")