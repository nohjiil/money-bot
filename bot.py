import os
import requests
import base64
from datetime import datetime

# 🔑 설정
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USER_ID = "nohjiil"
REPO_NAME = "money-bot"
FILE_PATH = "data.txt"

API_URL = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/{FILE_PATH}"


def get_file_sha():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(API_URL, headers=headers)

    if res.status_code == 200:
        return res.json()["sha"]
    return None


def collect_data():
    """
    👉 여기서 실제 데이터 구성
    지금은 안정적으로 '동작하는 구조'부터 만든다
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    data = [
        f"📅 업데이트 시간: {now}",
        "",
        "💰 오늘 참여 가능한 이벤트",
        "",
        "토스 만보기 참여 가능",
        "토스 친구 켜기 이벤트 진행중",
        "",
        "네이버 포인트 뽑기 진행중",
        "",
        "카카오 퀴즈 참여 가능",
        "",
        "KB 오늘의 퀴즈 있음",
        "",
        "신한 퀴즈팡팡 참여 가능",
        "",
        "하나 출석 체크 가능",
    ]

    return "\n".join(data)


def update_github(content):
    sha = get_file_sha()

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    payload = {
        "message": "🤖 auto update data.txt",
        "content": encoded_content,
        "branch": "main"
    }

    if sha:
        payload["sha"] = sha

    res = requests.put(API_URL, headers=headers, json=payload)

    if res.status_code in [200, 201]:
        print("✅ 업데이트 성공")
    else:
        print("❌ 실패")
        print(res.text)


if __name__ == "__main__":
    content = collect_data()
    update_github(content)
