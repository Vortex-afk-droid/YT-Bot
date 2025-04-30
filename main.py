import requests
import subprocess
import os
import cv2
import pytesseract
import time

# === CONFIGURATION ===
API_KEY = 'AIzaSyA1mUYybcPjqjJdzb-dnDx8S1Q_Cte80VY'  # Your YouTube API key
CHANNEL_ID = 'UCVfoa1Z2urvG9vN2YxZ3hQQ'  # JJ Olatunji's channel ID
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1367247354918338652/1POxqoACsjOOT5xDpMSwsD9OMnpGo9J9MGlfnx9l0dne1rXXFA1ZUZ7jZPlIj-tm0mZU'  # Your Discord webhook URL
LAST_VIDEO_FILE = 'last_video_id.txt'


def get_latest_video_id():
    url = f'https://www.googleapis.com/youtube/v3/search?key={API_KEY}&channelId={CHANNEL_ID}&part=snippet,id&order=date&maxResults=1'
    response = requests.get(url).json()
    if 'items' in response and len(response['items']) > 0:
        return response['items'][0]['id'].get('videoId')
    return None


def already_processed(video_id):
    if os.path.exists(LAST_VIDEO_FILE):
        with open(LAST_VIDEO_FILE, 'r') as f:
            return f.read().strip() == video_id
    return False


def save_last_video_id(video_id):
    with open(LAST_VIDEO_FILE, 'w') as f:
        f.write(video_id)


def download_video(video_id):
    url = f'https://www.youtube.com/watch?v={video_id}'
    subprocess.run(['yt-dlp', '-f', 'mp4', '-o', 'video.mp4', url])


def extract_text_from_video(path='video.mp4'):
    cap = cv2.VideoCapture(path)
    text_results = set()
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * 1)  # Every 1 second

    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if count % frame_interval == 0:
            text = pytesseract.image_to_string(frame)
            clean_text = text.strip()
            if clean_text:
                text_results.add(clean_text)
        count += 1
    cap.release()
    return list(text_results)


def send_to_discord(text_list):
    if not text_list:
        return
    text = '\n'.join(text_list)
    chunks = [text[i:i + 1900] for i in range(0, len(text), 1900)]
    for chunk in chunks:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": chunk})


def check_youtube_and_process():
    print("Checking for new video...")
    video_id = get_latest_video_id()
    if video_id and not already_processed(video_id):
        print(f"New video found: {video_id}")
        download_video(video_id)
        print("Downloaded video. Extracting text...")
        text = extract_text_from_video()
        print(f"Found {len(text)} text entries. Sending to Discord...")
        send_to_discord(text)
        save_last_video_id(video_id)
        print("Done.")
    else:
        print("No new video.")


# === AUTO LOOP EVERY 10 MINUTES ===
while True:
    check_youtube_and_process()
    time.sleep(600)
