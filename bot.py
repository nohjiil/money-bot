import requests, base64, os, re, time
from bs4 import BeautifulSoup
from datetime import datetime

print("🔥 BOT 실행됨")

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"

def clean(t):
    return re.sub(r'\s+', ' ', t).strip()

def is_valid(ans):
    if not ans: return False
    if len(ans) < 2: return False
    if ans in ["정보","확인","클릭","내용","보기","바로가기","-"]: return False
    return True

def find_answer(title, body):
    # 제목
    t = re.search(r'(정답|답)[\s:]*([^\s\[\]\(\)<>]{1,10})', title)
    if t and is_valid(t.group(2)):
        return t.group(2)

    # 본문
    patterns = [
        r'(정답|답|정답은|답은)\s*[:=]?\s*([^\s,.\[\]<>]{1,10})',
        r'▶\s*([^\s]{2,10})',
        r'☞\s*([^\s]{2,10})'
    ]

    for p in patterns:
        m = re.search(p, body)
        if m:
            ans = m.group(len(m.groups()))
            if is_valid(ans):
                return ans

    return None

def crawl():
    headers = {'User-Agent': 'Mozilla/5.0'}

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

                try:
                    time.sleep(0.7)
                    r = requests.get(url, headers=headers, timeout=7)
                    if "ppomppu" in url:
                        r.encoding = 'euc-kr'

                    ps = BeautifulSoup(r.text, 'html.parser')
                    for s in ps(['script','style','img','iframe']):
                        s.decompose()

                    body = clean(ps.get_text())[:2000]

                    ans = find_answer(title, body)

                    # 🔥 핵심: 정답 없으면 버림
                    if not ans:
                        continue

                    results.append(f"• {title[:40]} [정답: {ans}]")

                    if len(results) >= 20:
                        return results

                except:
                    continue

        except:
            continue

    return results


def upload(text):
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None

    content = base64.b64encode(text.encode()).decode()

    data = {
        "message": "update",
        "content": content
    }

    if sha:
        data["sha"] = sha

    r = requests.put(url, headers=headers, json=data)
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
        text += "⏳ 정답 포함 글 없음"

    upload(text)


if __name__ == "__main__":
    run()
