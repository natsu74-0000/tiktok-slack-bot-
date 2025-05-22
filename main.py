import requests
import time
import json
import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path

SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/XXX/YYY/ZZZ'  # 置き換え必須
USERNAME = 'syukanrfuc7'
SEEN_COMMENTS_FILE = Path('seen_comments.txt')
NIGHT_BUFFER_FILE = Path('data/night_buffer.json')


def get_latest_video_url():
    url = f'https://www.tiktok.com/@{USERNAME}'
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    links = soup.find_all('a', href=True)
    for link in links:
        href = link['href']
        if f'/@{USERNAME}/video/' in href:
            return href
    return None


def get_comments(video_url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.get(video_url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    comments = soup.find_all('p')
    return [c.get_text() for c in comments if c.get_text().strip()]


def load_seen_comments():
    if not SEEN_COMMENTS_FILE.exists():
        return set()
    return set(SEEN_COMMENTS_FILE.read_text().splitlines())


def save_seen_comments(comments):
    SEEN_COMMENTS_FILE.write_text('\n'.join(comments))


def send_slack_notification(comment):
    data = {'text': f'🗨 新しいTikTokコメント: "{comment}"'}
    requests.post(SLACK_WEBHOOK_URL, json=data)


def is_night_time():
    now = datetime.datetime.now()
    return now.hour < 9


def is_9am():
    now = datetime.datetime.now()
    return now.hour == 9 and now.minute == 0


def load_night_buffer():
    if NIGHT_BUFFER_FILE.exists():
        return json.loads(NIGHT_BUFFER_FILE.read_text())
    return []


def save_night_buffer(comments):
    NIGHT_BUFFER_FILE.write_text(json.dumps(comments, ensure_ascii=False))


def clear_night_buffer():
    if NIGHT_BUFFER_FILE.exists():
        NIGHT_BUFFER_FILE.unlink()


if __name__ == '__main__':
    print("✅ コメントチェック開始")
    video_url = get_latest_video_url()
    if not video_url:
        print("⚠️ 動画が見つかりません")
        exit()

    seen_comments = load_seen_comments()
    current_comments = get_comments(video_url)
    new_comments = [c for c in current_comments if c not in seen_comments]

    if is_9am():
        print("☀ 朝9時：夜間のコメントを通知中")
        night_comments = load_night_buffer()
        for c in night_comments:
            send_slack_notification(c)
        clear_night_buffer()
    elif is_night_time():
        print("🌙 夜間：通知は保留")
        buffer = load_night_buffer()
        buffer.extend(new_comments)
        save_night_buffer(buffer)
    else:
        for c in new_comments:
            send_slack_notification(c)

    save_seen_comments(current_comments)
