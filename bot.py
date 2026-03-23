import requests, base64, os, re, time
from bs4 import BeautifulSoup
from datetime import datetime

print("🔥 BOT 실행됨")

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"

headers = {'User-Agent': 'Mozilla/5.0'}

def clean(t):
    return re.sub(r'\s+', ' ', t).strip()

def is_valid(ans):
    if not ans: return False
    if len(ans) < 2: return False
    if ans in ["정보","확인","클릭","내용","보기","바로가기","-"]: return False
    return True

def extract_answer_from_text(text):
    patterns = [
        r'(정답|답|정답은|답은)\s*[:=]?\s*([^\s,.\[\]<>]{1,10})',
        r'▶\s*([^\s]{2,10})',
        r'☞\s*([^\s]{2,10})'
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            ans = m.group(len(m.groups()))
            if is_valid(ans):
                return ans
    return None


def get_answer(title, url):
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if "ppomppu" in url:
            res.encoding = 'euc-kr'

        soup = BeautifulSoup(res.text, 'html.parser')

        # 불필요 제거
        for s in soup(['script','style','img','iframe']):
            s.decompose()

        body = clean(soup.get_text())[:3000]

        # 1️⃣ 제목
        t = extract_answer_from_text(title)
        if t:
            return t

        # 2️⃣ 본문
        b = extract_answer_from_text(body)
        if b:
            return b

        # 3️⃣ 댓글 (핵심 추가)
        comments = soup.select('.commentContent, .comment_content, td.comment')
        for c in comments:
            txt = clean(c.get_text())
            a = extract_answer_from_text(txt)
            if a:
                return a

    except:
        pass

    return None


def crawl():
    targets = [
        {"url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
        {"url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"}
    ]

    include = ["토스","네이버","카카오","KB","신한","하나","페이","퀴즈"]

    results = []

    for t in targets:
        try:
            res = requests.get(t['url'], headers=headers, timeout=10)
            if "ppomppu" in t['url']:
                res.encoding = 'euc-kr'

            soup = BeautifulSoup(res.text, 'html.parser')

            for a in soup.select('a'):
                title = clean(a.get_text())
                href = a.get('href','')

                if len(title) < 6:
                    continue
                if not any(k in title for k in include):
                    continue

                url = href if href.startswith('http') else t['base'] + href

                time.sleep(0.6)

                ans = get_answer(title, url)

                # ✔ 정답 있으면 우선
                if ans:
                    results.append(f"• {title[:40]} [정답: {ans}]")
                else:
                    # ✔ fallback (너가 원해서 유지)
                    results.append(f"• {title[:40]} [확인필요]")

                if len(results) >= 25:
                    return results

        except:
            continue

    return results


def upload(text):
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"

    headers_git = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    res = requests.get(url, headers=headers_git)
    sha = res.json().get("sha") if res.status_code == 200 else None

    content = base64.b64encode(text.encode()).decode()

    data = {
        "message": "update",
        "content": content
    }

    if sha:
        data["sha"] = sha

    r = requests.put(url, headers=headers_git, json=data)
    print("업로드:", r.status_code)


def run():
    items = crawl()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    text = f"""📅 업데이트 시간: {now}

✅ 실시간 포인트 정보 (정답/적립)
----------------------------------
"""

    if items:
        text += "\n".join(items)
    else:
        text += "⏳ 데이터 없음"

    upload(text)


if __name__ == "__main__":
    run()
