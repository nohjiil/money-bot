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


# ✅ 허용 키워드 (핵심 앱만)
ALLOW_KWS = [
    "카카오", "KB", "신한", "하나",
    "토스", "네이버", "OK캐시백"
]


# ✅ 정답 추출 (강화 버전)
def extract_answer(body, title):

    body = body.replace("\n", " ")

    patterns = [
        r'정답\s*[:\-]?\s*([가-힣A-Za-z0-9]{1,20})',
        r'정답은\s*([가-힣A-Za-z0-9]{1,20})',
        r'답은\s*([가-힣A-Za-z0-9]{1,20})',
        r'👉\s*([가-힣A-Za-z0-9]{1,20})',
        r'☞\s*([가-힣A-Za-z0-9]{1,20})',
    ]

    for p in patterns:
        m = re.search(p, body)
        if m:
            ans = m.group(1)
            ans = re.sub(r'(입니다|입니다\.|요)$', '', ans)
            ans = ans.strip()

            if ans not in ["확인", "내용", "링크"]:
                return ans

    # 숫자형
    m = re.search(r'(\d+)번', body)
    if m:
        return m.group(1) + "번"

    # OX
    if "OX" in title:
        return "O/X형"

    return ""


# ✅ 크롤링
def get_real_data():

    url = "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon"
    base = "https://www.ppomppu.co.kr/zboard/"
    headers = {'User-Agent': 'Mozilla/5.0'}

    found = []
    seen = set()

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')

        for a in soup.select('a[href*="view.php"]'):

            title_txt = a.get_text().strip()
            href = a.get('href', '')

            # 🔥 퀴즈만
            if "퀴즈" not in title_txt:
                continue

            # 🔥 정답글 제외
            if "정답" in title_txt:
                continue

            # 🔥 허용 앱만 통과
            if not any(k in title_txt for k in ALLOW_KWS):
                continue

            # 🔥 중복 제거
            key = title_txt[:20]
            if key in seen:
                continue
            seen.add(key)

            full_url = href if href.startswith('http') else base + href

            try:
                time.sleep(0.7)

                p_res = requests.get(full_url, headers=headers, timeout=10)
                p_res.encoding = 'euc-kr'
                p_soup = BeautifulSoup(p_res.text, 'html.parser')

                # 불필요 제거
                for s in p_soup(['script', 'style']):
                    s.decompose()

                body = p_soup.get_text(" ")
                body = re.sub(r'\s+', ' ', body)

                ans = extract_answer(body, title_txt)
                clean_t = title_txt[:25]

                # ✅ UX
                if not ans:
                    found.append(f"• [{clean_t}] 👉 <a href='{full_url}'>정답확인하기</a>")
                else:
                    found.append(f"• [{clean_t}] [정답: {ans}]")

            except:
                found.append(f"• [{title_txt[:25]}] 👉 <a href='{full_url}'>확인하기</a>")

            if len(found) >= 20:
                break

    except:
        return ["❌ 전체 크롤링 실패"]

    return found


# ✅ 실행
items = get_real_data()

now_kst = datetime.utcnow() + timedelta(hours=9)
now_str = now_kst.strftime("%Y-%m-%d %H:%M")

header = f"🗓️ 업데이트 시간: {now_str} (한국시간)\n\n🎁 포인트 올인원 매니저\n------------------------\n\n"

body = "<br>".join(items) if items else "⏳ 없음"

final_text = header + body

print("🔥 BOT 실행됨")


# ✅ GitHub 업로드
url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
headers = {"Authorization": f"token {TOKEN}"}

res = requests.get(url, headers=headers)
sha = res.json().get("sha") if res.status_code == 200 else None

encoded = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')

data = {
    "message": "final bot (필터 + UX + 안정성)",
    "content": encoded,
    "branch": BRANCH
}

if sha:
    data["sha"] = sha

requests.put(url, headers=headers, json=data)

print("🚀 업로드 완료")