import requests
import base64
from datetime import datetime

# =====================
# 설정
# =====================
REPO = "nohjiil/money-bot"
FILE_PATH = "data.txt"
BRANCH = "main"

TOKEN = __import__("os").environ.get("GITHUB_TOKEN")

# =====================
# 데이터 (여기에 너가 만든 리스트 넣으면 됨)
# =====================
items = [
    "• [토스]260324 토스 버튼 눌러 1등 만들기 [정답: 만들기]",
    "• [네이버페이]라방 9원, 토스트 1~3원 [정답: 라방]",
    "• [카카오뱅크]OX 퀴즈 3/24 정답 [정답: 정답]",
    "• [KB스타뱅킹]스타퀴즈 정답 [정답: 정답]",
]

# =====================
# 텍스트 생성
# =====================
now = datetime.now().strftime("%Y-%m-%d %H:%M")

header = f"""📅 업데이트 시간: {now}

✅ 실시간 포인트 정보 (정답/적립)
----------------------------------
"""

body = "\n".join(items) if items else "⏳ 정보 수집 중..."

final_text = header + body

print("🔥 BOT 실행됨")
print(final_text)

# =====================
# 기존 파일 SHA 가져오기
# =====================
url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json"
}

res = requests.get(url, headers=headers)

sha = None
if res.status_code == 200:
    sha = res.json()["sha"]

# =====================
# 업로드
# =====================
encoded = base64.b64encode(final_text.encode()).decode()

data = {
    "message": "update",
    "content": encoded,
    "branch": BRANCH
}

if sha:
    data["sha"] = sha

res = requests.put(url, headers=headers, json=data)

print("📡 업로드 결과:", res.status_code)
print(res.text)
