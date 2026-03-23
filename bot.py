import os
import requests
import base64
from datetime import datetime

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


# ✅ 핵심: 텍스트 정리 필터
def clean_text(raw_text):
    lines = raw_text.split("\n")
    cleaned = []

    for line in lines:
        line = line.strip()

        # ❌ 필요 없는 것 제거
        if not line:
            continue
        if "미리보기" in line:
            continue
        if "공유용" in line:
            continue
        if len(line) < 5:
            continue

        # ✔️ 앞에 점/특수문자 제거
        line = line.replace("•", "").strip()

        cleaned.append(line)

    return cleaned


# 👉 여기 실제 데이터 넣으면 됨 (지금은 테스트용)
def get_raw_data():
    return """
• [네이버페이]지난쇼라 1원들
• [네이버페이]19시 쇼라 5원들
• [네이버페이]배민클럽 15원
• [카카오뱅크]260323 카카오뱅크 Ai 이모
• [네이버페이]11시 쇼라 5원들
• [네이버페이]10시 쇼라 5원
• [KB Pay] 오늘의 퀴즈 3/23일자 정답
• [카카오페이]퀴즈
• [네이버페이]9시 쇼라 5원
• [네이버페이]후디스펫 브랜드스토어 100원 받
• [카카오뱅크]AI 퀴즈
• [토스]260323 토스알바 밸런스게임 팀플전
• [네이버페이]요기요 등 13원 받으세요
• [토스]260323 토스 버튼 눌러 1등 만들기
• [토스]260323 토스 두근두근 1등 찍기
• [네이버페이]이번 주 카페 결제 적립 신청
• [카카오뱅크]OX 퀴즈 3/23 정답
• [하나원큐]슬기로운 금융생활 OX퀴즈 정답
• 토스 및 네이버 페이왕 관련 이벤트 공유용 게시글
"""


def make_content():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    raw = get_raw_data()
    cleaned = clean_text(raw)

    lines = [
        f"📅 업데이트 시간: {now}",
        "",
        "✅ 실시간 포인트 정보 (정답/적립)",
        "----------------------------------",
    ]

    for item in cleaned:
        lines.append(f"• {item}")

    return "\n".join(lines)


def update_github(content):
    sha = get_file_sha()

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    data = {
        "message": "clean update",
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


if __name__ == "__main__":
    content = make_content()
    update_github(content)
