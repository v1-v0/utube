from pathlib import Path
import pandas as pd
import csv
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from datetime import datetime
from zoneinfo import ZoneInfo

# Load environment variables
load_dotenv()
GOOGLE_KEY = os.getenv("googleKey")
if not GOOGLE_KEY:
    print("Google API key not found. Please set it in your .env file.")
    exit(1)

# Initialize YouTube API client
youtube = build("youtube", "v3", developerKey=GOOGLE_KEY)

# File paths
watchLaterVideo = Path("playlists") / "Watch later videos.csv"
if not watchLaterVideo.exists() or watchLaterVideo.suffix != '.csv':
    print(f"Invalid file: {watchLaterVideo}")
    exit(1)

# Function to fetch channel info
def get_channel_info(video_id):
    try:
        video_response = youtube.videos().list(part="snippet", id=video_id).execute()
        if video_response['items']:
            return {
                "title": video_response["items"][0]["snippet"]["title"],
                "channelId": video_response["items"][0]["snippet"]["channelId"],
                "channelTitle": video_response["items"][0]["snippet"]["channelTitle"]
            }
    except Exception as e:
        print(f"API Error for video {video_id}: {str(e)}")
    return None

# Read CSV and process data
ids, urls, created_dates = [], [], []
with open(watchLaterVideo, 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        if 'Video ID' in row and 'Playlist video creation timestamp' in row:
            try:
                ids.append(row['Video ID'])
                urls.append('https://www.youtube.com/watch?v=' + row['Video ID'])
                timestamp = row['Playlist video creation timestamp']
                dt = datetime.fromisoformat(timestamp).astimezone(ZoneInfo("Asia/Hong_Kong"))
                created_dates.append(dt.strftime('%Y-%m-%d %H:%M:%S'))
            except ValueError:
                print(f"Skipping row with invalid timestamp: {row}")
        else:
            print(f"Skipping row with missing columns: {row}")

# Fetch channel info
channel_info_dict = {}
for video_id in ids:
    info = get_channel_info(video_id)
    if info:
        channel_info_dict[video_id] = info

# Create DataFrame
df = pd.DataFrame([
    {
        'Video ID': video_id,
        'Video URL': urls[idx],
        'Video Creation Date': created_dates[idx],
        'Video Title': info['title'],
        'Channel ID': info['channelId'],
        'Channel Title': info['channelTitle']
    } for idx, (video_id, info) in enumerate(channel_info_dict.items())
])

# Save to Excel
output_dir = Path("~/Downloads").expanduser()
output_dir.mkdir(parents=True, exist_ok=True)
p = output_dir / "WatchlaterPlaylist.xlsx"
df.to_excel(p, index=False, engine='openpyxl')
print(f"Channel info saved to {p}")