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

    # 숫자형 (1번 등)
    m2 = re.search(r'(\d+)번', body)
    if m2:
        return m2.group(1) + "번"

    # OX
    if "OX" in title:
        return "O/X형"

    # 글자수 힌트
    if re.search(r'\(\d+글자\)', title):
        return "주관식"

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

            if any(e in title_txt for e in exclude_kws):
                continue

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

                # 🔥 본문 + 댓글까지 포함
                text_blocks = []

                # 본문
                text_blocks.append(p_soup.get_text(" "))

                # 댓글 영역 (뽐뿌)
                comments = p_soup.select('.board-comment, .comment_list, .commentContent')
                for c in comments:
                    text_blocks.append(c.get_text(" "))

                body = " ".join(text_blocks)
                body = re.sub(r'\s+', ' ', body)

                ans = extract_answer(body, title_txt)

                clean_t = title_txt[:25]

                if not ans:
                    found.append(f"• {clean_t} [확인 필요]")
                    continue

                found.append(f"• {clean_t} [정답: {ans}]")

            except:
                clean_t = title_txt[:25]
                found.append(f"• {clean_t} [실패]")
                continue

            if len(found) >= 20:
                break

    except:
        return ["❌ 전체 실패"]

    return found


items = get_real_data()

now_kst = datetime.utcnow() + timedelta(hours=9)
now_str = now_kst.strftime("%Y-%m-%d %H:%M")

header = f"🗓️ 업데이트 시간: {now_str} (한국시간)\n\n✅ 퀴즈 정보 (최종 모드)\n------------------------\n\n"
body = "<br>".join(items) if items else "⏳ 없음"
final_text = header + body

print("🔥 BOT 실행됨")

url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
h = {"Authorization": f"token {TOKEN}"}

res = requests.get(url, headers=h)
sha = res.json().get("sha") if res.status_code == 200 else None

encoded = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')

data = {
    "message": "final: 댓글까지 포함한 정답 추출",
    "content": encoded,
    "branch": BRANCH
}

if sha:
    data["sha"] = sha

requests.put(url, headers=h, json=data)
print("🚀 업로드 완료")
