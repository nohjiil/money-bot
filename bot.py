import requests
import base64
from datetime import datetime, timedelta
import os
import re
import time
from bs4 import BeautifulSoup

REPO = "nohjiil/money-bot"
FILE_PATH = "data.txt"
BRANCH = "main"
TOKEN = os.environ.get("GITHUB_TOKEN")


def extract_answer(body, title):

    # 1차: 정형 패턴
    patterns = [
        r'정답[\s:]*["“]?([가-힣A-Za-z0-9]{1,15})',
        r'정답은\s*["“]?([가-힣A-Za-z0-9]{1,15})',
        r'답은\s*["“]?([가-힣A-Za-z0-9]{1,15})',
        r'\[정답\]\s*([가-힣A-Za-z0-9]{1,15})',
        r'([가-힣A-Za-z0-9]{1,15})\s*-\s*정답'
    ]

    for p in patterns:
        m = re.search(p, body)
        if m:
            ans = m.group(1).strip()
            ans = re.sub(r'(입니다|요|입니다\.)$', '', ans)

            if ans not in ["정답", "확인", "내용"]:
                return ans

    # 2차: 짧은 단어 후보 (🔥 핵심)
    candidates = re.findall(r'\b[가-힣]{2,6}\b', body)

    blacklist = [
        "쿠폰", "게시판", "로그인", "추천", "조회", "댓글",
        "이벤트", "오늘", "정보", "공유", "내용", "확인"
    ]

    for c in candidates[:80]:
        if c not in blacklist:
            return c

    # 3차: 숫자형
    m2 = re.search(r'(\d+)번', body)
    if m2:
        return m2.group(1) + "번"

    # 4차: OX
    if "OX" in title:
        return "O/X형"

    return ""


def get_real_data():
    url = "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon"
    base = "https://www.ppomppu.co.kr/zboard/"
    headers = {'User-Agent': 'Mozilla/5.0'}

    exclude_kws = ["모니모", "출석", "만보기", "쇼핑", "핫딜"]

    found = []
    seen = set()

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')

        for a in soup.select('a[href*="view.php"]'):
            title_txt = a.get_text().strip()
            href = a.get('href', '')

            # 퀴즈만
            if "퀴즈" not in title_txt:
                continue

            # 정답글 제외
            if "정답" in title_txt:
                continue

            # 이모지/AI 문제 제거
            if any(x in title_txt.lower() for x in ["이모", "이모지", "emoji"]):
                continue

            # 불필요 필터
            if any(e in title_txt for e in exclude_kws):
                continue

            # 중복 제거
            key = title_txt[:20]
            if key in seen:
                continue
            seen.add(key)

            full_url = href if href.startswith('http') else base + href

            try:
                time.sleep(0.8)
                p_res = requests.get(full_url, headers=headers, timeout=10)
                p_res.encoding = 'euc-kr'
                p_soup = BeautifulSoup(p_res.text, 'html.parser')

                # 불필요 제거
                for s in p_soup(['script', 'style', 'img']):
                    s.decompose()

                # 본문 + 댓글
                text_blocks = []
                text_blocks.append(p_soup.get_text(" "))

                comments = p_soup.select('.board-comment, .comment_list, .commentContent')
                for c in comments:
                    text_blocks.append(c.get_text(" "))

                body = " ".join(text_blocks)
                body = re.sub(r'\s+', ' ', body)

                # 🔥 디버깅 필요하면 이거 켜라
                # print(body[:300])

                ans = extract_answer(body, title_txt)
                clean_t = title_txt[:25]

                # UX 처리
                if not ans:
                    found.append(f"• {clean_t} 👉 <a href='{full_url}' style='color:blue;font-weight:bold;'>정답확인하기</a>")
                else:
                    found.append(f"• {clean_t} [정답: {ans}]")

            except:
                found.append(f"• {title_txt[:25]} 👉 <a href='{full_url}'>확인필요</a>")

            if len(found) >= 20:
                break

    except:
        return ["❌ 전체 실패"]

    return found


# 실행
items = get_real_data()

now_kst = datetime.utcnow() + timedelta(hours=9)
now_str = now_kst.strftime("%Y-%m-%d %H:%M")

header = f"🗓️ 업데이트 시간: {now_str} (한국시간)\n\n🎁 포인트 올인원 매니저\n------------------------\n\n"
body = "<br>".join(items) if items else "⏳ 없음"
final_text = header + body

print("🔥 BOT 실행됨")

# GitHub 업로드
url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
h = {"Authorization": f"token {TOKEN}"}

res = requests.get(url, headers=h)
sha = res.json().get("sha") if res.status_code == 200 else None

encoded = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')

data = {
    "message": "final stable version (pattern + fallback + UX)",
    "content": encoded,
    "branch": BRANCH
}

if sha:
    data["sha"] = sha

requests.put(url, headers=h, json=data)
print("🚀 업로드 완료")
