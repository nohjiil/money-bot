import os, requests, base64
from datetime import datetime

print("🔥 CLEAN UPDATE 실행")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USER_ID = "nohjiil"
REPO_NAME = "money-bot"
FILE_PATH = "data.txt"

API_URL = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/{FILE_PATH}"


def make_content():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return "\n".join([
        f"📅 업데이트 시간: {now}",
        "",
        "✅ 실시간 포인트 정보 (정답/적립)",
        "----------------------------------",
        "• 토스 테스트",
        "• 네이버 테스트",
        "• 카카오 테스트",
        "• KB 테스트",
        "• 신한 테스트",
        "• 하나 테스트"
    ])


def update():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # 👉 기존 파일 무조건 가져오기
    res = requests.get(API_URL, headers=headers)

    if res.status_code == 200:
        sha = res.json()["sha"]
    else:
        sha = None

    content = make_content()
    encoded = base64.b64encode(content.encode()).decode()

    data = {
        "message": "🔥 FORCE CLEAN UPDATE",
        "content": encoded,
        "sha": sha  # 👉 반드시 포함 (덮어쓰기 핵심)
    }

    res = requests.put(API_URL, headers=headers, json=data)

    print("📡 상태:", res.status_code)
    print(res.text)


if __name__ == "__main__":
    update()
