import os
import requests
import base64
from datetime import datetime
from bs4 import BeautifulSoup

# 🔑 설정
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USER_ID = "nohjiil"
REPO_NAME = "money-bot"
FILE_PATH = "data.txt"

API_URL = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/{FILE_PATH}"


# 📌 기존 파일 SHA 가져오기
def get_file_sha():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(API_URL, headers=headers)

    if res.status_code == 200:
        return res.json()["sha"]
    return None


# 📌 뽐뿌 크롤링
def fetch_ppomppu():
    url = "https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers, timeout=10)
    res.encoding = "euc-kr"

    return res.text


# 📌 제목 추출 + 필터링
def extract_titles(html):
    soup = BeautifulSoup(html, "html.parser")

    results = []
    seen = set()

    for a in soup.select("a"):
        text = a.get_text(strip=True)

        # 🔥 핵심 필터 (돈 되는 키워드만)
        if not any(k in text for k in ["토스", "네이버", "카카오", "KB", "신한", "하나"]):
            continue

        # ❌ 제거 대상
        if "미리보기" in text:
            continue
        if "댓글" in text:
            continue
        if len(text) < 8:
            continue

        # 중복 제거
        if text in seen:
            continue
        seen.add(text)

        results.append(text)

    return results[:25]  # 최대 25개


# 📌 data.txt 생성
def make_content():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        html = fetch_ppomppu()
        titles = extract_titles(html)

        if not titles:
            titles = ["❌ 데이터를 가져오지 못했습니다"]

    except Exception as e:
        titles = [f"❌ 오류 발생: {str(e)}"]

    lines = [
        f"📅 업데이트 시간: {now}",
        "",
        "✅ 실시간 포인트 정보 (정답/적립)",
        "----------------------------------",
    ]

    for t in titles:
        lines.append(f"• {t}")

    return "\n".join(lines)


# 📌 GitHub 업데이트
def update_github(content):
    sha = get_file_sha()

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    data = {
        "message": "🤖 auto update (real data)",
        "content": encoded,
        "branch": "main"
    }

    if sha:
        data["sha"] = sha

    res = requests.put(API_URL, headers=headers, json=data)

    if res.status_code in [200, 201]:
        print("✅ 업데이트 성공")
    else:
        print("❌ 실패")
        print(res.text)


# 🚀 실행
if __name__ == "__main__":
    content = make_content()
    update_github(content)
