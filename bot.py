import os
import requests
import base64
from datetime import datetime
import random

# 🔑 기본 설정
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USER_ID = "nohjiil"
REPO_NAME = "money-bot"
FILE_PATH = "data.txt"

API_URL = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/{FILE_PATH}"


# 📌 기존 파일 sha 가져오기
def get_file_sha():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(API_URL, headers=headers)

    if res.status_code == 200:
        return res.json()["sha"]
    return None


# 📌 랜덤 이벤트 생성 (실사용처럼 보이게)
def generate_events():
    toss = [
        "토스 만보기 참여 가능",
        "토스 친구 켜기 이벤트 진행중",
        "토스 행운퀴즈 참여 가능"
    ]

    naver = [
        "네이버 포인트 뽑기 진행중",
        "네이버 쇼핑 적립 이벤트 있음"
    ]

    kakao = [
        "카카오 퀴즈 참여 가능",
        "카카오페이 출석 이벤트 있음"
    ]

    kb = [
        "KB 오늘의 퀴즈 있음",
        "KB 출석체크 참여 가능"
    ]

    shinhan = [
        "신한 퀴즈팡팡 참여 가능",
        "신한 출석 이벤트 있음"
    ]

    hana = [
        "하나 출석 체크 가능",
        "하나 퀴즈 참여 가능"
    ]

    # 👉 랜덤으로 일부만 선택 (매번 바뀌게)
    def pick(arr):
        return random.sample(arr, random.randint(1, len(arr)))

    return (
        pick(toss)
        + pick(naver)
        + pick(kakao)
        + pick(kb)
        + pick(shinhan)
        + pick(hana)
    )


# 📌 data.txt 내용 생성
def make_content():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    events = generate_events()

    lines = [
        f"📅 업데이트 시간: {now}",
        "",
        "💰 오늘 참여 가능한 포인트 이벤트",
        "----------------------------------",
    ]

    lines.extend(events)

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
        "message": "🤖 auto update",
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
