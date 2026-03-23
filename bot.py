import os, requests, base64
from datetime import datetime

print("🔥🔥🔥 BOT 실행됨 🔥🔥🔥")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USER_ID = "nohjiil"
REPO_NAME = "money-bot"

url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"

def run():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    text = f"""🔥 업데이트 성공 🔥
시간: {now}
"""

    print("📡 업로드 시작")

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    res = requests.get(url, headers=headers)
    sha = res.json()["sha"] if res.status_code == 200 else None

    content = base64.b64encode(text.encode()).decode()

    data = {
        "message": "update",
        "content": content
    }

    if sha:
        data["sha"] = sha

    res = requests.put(url, headers=headers, json=data)

    print("결과:", res.status_code)
    print(res.text)


if __name__ == "__main__":
    run()
