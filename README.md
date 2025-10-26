# YouTube Drive Downloader (Merged)

A combined tool to download YouTube videos/playlists and scrape/download Google Drive links from YouTube videos.

## Features

- **YouTube Video Downloading**: Download videos or playlists in various formats (mp4, mp3, wav) with quality and speed options.
- **Google Drive Link Scraping**: Extract Google Drive file/folder links from video descriptions and comments, then download them.
- **Search and Playlists**: Search for videos/playlists or provide direct URLs.
- **Video Fixing**: Re-encode downloaded MP4s for compatibility.
- **Configuration**: Use .env file for default settings.

## Install

```bash
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

## .env (optional)

Copy the provided example:

```bash
copy example.env .env
```

Edit `.env` and set values:

```
YOUTUBE_URL=https://www.youtube.com/watch?v=VIDEO_ID
OUTPUT_DIR=downloads
MAX_COMMENTS=200
TIMEOUT=20
```

If you run with `-l`, it will be saved to `.env` automatically.

## Usage

### Basic Video Download

Download a single video:

```bash
python app.py -l "https://www.youtube.com/watch?v=VIDEO_ID"
```

Download with specific format and quality:

```bash
python app.py -l "https://www.youtube.com/watch?v=VIDEO_ID" -f mp4 -q 720p
```

Download audio:

```bash
python app.py -l "https://www.youtube.com/watch?v=VIDEO_ID" -f mp3
```

### Playlist Download

Download a playlist:

```bash
python app.py -l "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

### Search

Search for a video:

```bash
python app.py -s "search query"
```

### Drive Links

Download a video and scrape Drive links:

```bash
python app.py -l "https://www.youtube.com/watch?v=VIDEO_ID" --drive
```

### Fix Videos

Fix downloaded MP4s:

```bash
python app.py -f fix
```

### Options

- `-s, --search`: Search query for video or playlist
- `-l, --link`: Direct YouTube URL
- `-f, --format`: Format: mp3, mp4, wav, etc. (default: mp4). Use 'fix' to re-encode videos.
- `-q, --quality`: Quality: 240, 720, 1080, 4k, etc.
- `-u, --speed`: Playback speed: 0.5, 1.0, 1.5x, 2.0, etc. (default: 1.0)
- `--output`: Output directory (default: downloads)
- `--drive`: Scrape and download Google Drive links from the video
- `--max-comments`: Max comments to scan for Drive links (default: 200)
- `--timeout`: Timeout for requests (default: 20)

## Example

Download a YouTube video in 720p MP4 and scrape any Drive links:

```bash
python app.py -l "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -q 720p --drive --output my_videos
```

This will download the video to `my_videos/` and any Google Drive files/folders linked in the video's description or comments.

## Notes

- Publicly accessible Drive links work best. For restricted files, ensure you have access.
- Folder downloads replicate the Drive folder structure under the output directory.
- Use responsibly and comply with YouTube and Google Drive terms.

## Disclaimer

Use responsibly and comply with YouTube and Google Drive terms. This tool is for personal/educational purposes.