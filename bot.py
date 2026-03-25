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

def get_real_data():
    url = "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon"
    base = "https://www.ppomppu.co.kr/zboard/"
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 🔥 제외 대상
    exclude_kws = ["모니모", "출석", "만보기", "쇼핑", "핫딜"]

    found = []

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')

        # 🔥 게시글만
        for a in soup.select('a[href*="view.php"]'):
            title_txt = a.get_text().strip()
            href = a.get('href', '')

            # 🔥 퀴즈만
            if "퀴즈" not in title_txt:
                continue

            # 🔥 제외 키워드
            if any(e in title_txt for e in exclude_kws):
                continue

            if len(title_txt) < 6:
                continue

            full_url = href if href.startswith('http') else base + href
            ans = ""

            try:
                time.sleep(0.8)
                p_res = requests.get(full_url, headers=headers, timeout=10)
                p_res.encoding = 'euc-kr'
                p_soup = BeautifulSoup(p_res.text, 'html.parser')

                for s in p_soup(['script', 'style', 'img']):
                    s.decompose()

                body = p_soup.get_text(" ")
                body = re.sub(r'\s+', ' ', body)

                # 🔥 정답 추출
                m = re.search(r'(정답|답)[\s:]*([^\s,.<>]{1,10})', body)
                if m:
                    ans = m.group(2).strip()

                ans = ans.replace("(", "").replace(")", "").strip()

                # 🔥 쓰레기 값 제거
                if ans in ["정보", "내용", "확인", "참고", "이벤트", "공지"]:
                    ans = ""

                if ans:
                    info = f" [정답: {ans}]"
                else:
                    preview = re.sub(r'^[^가-힣a-zA-Z0-9]+', '', body)
                    info = f" [미리보기: {preview[:25]}...]"

            except:
                info = " [에러]"

            clean_t = title_txt[:25]
            found.append(f"• {clean_t}{info}")

            if len(found) >= 20:
                break

    except:
        return ["❌ 크롤링 실패"]

    return found


items = get_real_data()

now_kst = datetime.utcnow() + timedelta(hours=9)
now_str = now_kst.strftime("%Y-%m-%d %H:%M")

header = f"🗓️ 업데이트 시간: {now_str} (한국시간)\n\n✅ 퀴즈 정보\n------------------------\n\n"
body = "<br>".join(items) if items else "⏳ 없음"
final_text = header + body

print("🔥 BOT 실행됨")

url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
h = {"Authorization": f"token {TOKEN}"}

res = requests.get(url, headers=h)
sha = res.json().get("sha") if res.status_code == 200 else None

encoded = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
data = {
    "message": "fix: quiz filter + garbage answer 제거",
    "content": encoded,
    "branch": BRANCH
}
if sha:
    data["sha"] = sha

res = requests.put(url, headers=h, json=data)
print("🚀 업로드:", res.status_code)