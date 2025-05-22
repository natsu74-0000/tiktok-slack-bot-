import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Slack Webhook URL
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/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'

# TikTokの対象ユーザー
USERNAME = 'syukanrfuc7'

# コメント履歴保存ファイル
SEEN_COMMENTS_FILE = 'seen_comments.txt'

def get_latest_video_url():
    url = f'https://www.tiktok.com/@{USERNAME}'
    print(f"🌐 TikTokプロフィールを開く: {url}")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    video_links = soup.find_all('a', href=True)
    for link in video_links:
        href = link['href']
        if f'/@{USERNAME}/video/' in href:
            print(f"🎥 見つかった動画URL: {href}")
            return href
    return None

def get_comments(video_url):
    print(f"💬 コメント取得中: {video_url}")
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
    try:
        with open(SEEN_COMMENTS_FILE, 'r') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_seen_comments(comments):
    with open(SEEN_COMMENTS_FILE, 'w') as f:
        for comment in comments:
            f.write(comment + '\n')

def send_slack_notification(comment):
    data = {'text': f'🗨 新しいTikTokコメント: "{comment}"'}
    requests.post(SLACK_WEBHOOK_URL, json=data)

if __name__ == '__main__':
    print("✅ コメントチェック開始")
    video_url = get_latest_video_url()

    if not video_url:
        print("⚠️ 動画が見つかりません")
        exit()

    seen_comments = load_seen_comments()
    current_comments = get_comments(video_url)

    new_comments = [c for c in current_comments if c not in seen_comments]
    if new_comments:
        print(f"✨ 新コメント {len(new_comments)} 件")
        for c in new_comments:
            send_slack_notification(c)
    else:
        print("🟢 新しいコメントなし")

    save_seen_comments(current_comments)
