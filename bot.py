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


def clean_title(title):
    title = re.sub(r'\s+', ' ', title)
    title = title.strip()
    return title[:30]


def extract_answer(body, title):
    patterns = [
        r'정답[\s:]*([가-힣A-Za-z0-9]{1,15})',
        r'답[\s:]*([가-힣A-Za-z0-9]{1,15})',
        r'정답은[\s:]*([가-힣A-Za-z0-9]{1,15})',
        r'답은[\s:]*([가-힣A-Za-z0-9]{1,15})'
    ]

    for p in patterns:
        m = re.search(p, body)
        if m:
            ans = m.group(1).strip()
            ans = re.sub(r'(은|는|을|를|이|가)$', '', ans)
            if ans not in ["정보", "내용", "확인", "-", "답"]:
                return ans

    # 숫자형
    m2 = re.search(r'(\d+)번', body)
    if m2:
        return m2.group(1) + "번"

    # OX
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

            if "퀴즈" not in title_txt:
                continue

            if "정답" in title_txt:
                continue

            if any(x in title_txt.lower() for x in ["이모", "이모지", "emoji"]):
                continue

            if any(e in title_txt for e in exclude_kws):
                continue

            key = title_txt[:20]
            if key in seen:
                continue
            seen.add(key)

            full_url = href if href.startswith('http') else base + href
            clean_t = clean_title(title_txt)

            try:
                time.sleep(0.8)
                p_res = requests.get(full_url, headers=headers, timeout=10)
                p_res.encoding = 'euc-kr'
                p_soup = BeautifulSoup(p_res.text, 'html.parser')

                for s in p_soup(['script', 'style', 'img']):
                    s.decompose()

                body = p_soup.get_text(" ")
                body = re.sub(r'\s+', ' ', body)

                ans = extract_answer(body, title_txt)

                if not ans:
                    found.append(f"• {clean_t} 👉 <a href='{full_url}' target='_blank'>정답확인하기</a>")
                else:
                    found.append(f"• {clean_t} [정답: {ans}]")

            except:
                # 🔥 실패도 클릭 가능하게 변경
                found.append(f"• {clean_t} 👉 <a href='{full_url}' target='_blank'>확인하기</a>")

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
    "message": "final stable UX version",
    "content": encoded,
    "branch": BRANCH
}

if sha:
    data["sha"] = sha

requests.put(url, headers=h, json=data)
print("🚀 업로드 완료")
