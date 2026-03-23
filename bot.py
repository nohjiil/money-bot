import os, requests, base64
from datetime import datetime

print("🔥🔥🔥 NEW VERSION RUNNING 🔥🔥🔥")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USER_ID = "nohjiil"
REPO_NAME = "money-bot"
FILE_PATH = "data.txt"

API_URL = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/{FILE_PATH}"


# 👉 강제 테스트용 데이터 (무조건 바뀌게)
def make_content():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"🔥 테스트 업데이트 성공 🔥",
        f"⏰ 시간: {now}",
        "",
        "✅ 이 문장이 보이면 GitHub 업데이트 성공한 거다",
        "",
        "토스 테스트",
        "네이버 테스트",
        "카카오 테스트",
        "KB 테스트",
        "신한 테스트",
        "하나 테스트"
    ]

    return "\n".join(lines)


def update_github(content):
    print("📦 업로드 시도")

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # 기존 파일 SHA 가져오기
    res = requests.get(API_URL, headers=headers)

    sha = None
    if res.status_code == 200:
        sha = res.json().get("sha")

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    data = {
        "message": "🔥 debug update",
        "content": encoded
    }

    if sha:
        data["sha"] = sha

    res = requests.put(API_URL, headers=headers, json=data)

    print("📡 상태코드:", res.status_code)

    if res.status_code in [200, 201]:
        print("✅ 업데이트 성공")
    else:
        print("❌ 실패:", res.text)


if __name__ == "__main__":
    content = make_content()
    update_github(content)
