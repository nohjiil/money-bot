import requests, base64, os, re, time
from bs4 import BeautifulSoup
from datetime import datetime

print("🔥 BOT 실행됨")

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def extract_answer(title, body):
    # ❌ 이상한 값 필터
    bad_words = ["정보", "클릭", "내용", "확인", "바로가기"]

    # 1️⃣ 제목에서 정답 추출 (끝부분)
    t = re.search(r'(정답|답)[\s:]*([^\s\[\]\(\)<>]{1,10})', title)
    if t:
        ans = t.group(2)
        if ans not in bad_words:
            return ans

    # 2️⃣ 본문에서 정답 찾기 (강력)
    patterns = [
        r'(정답|답|정답은|답은)\s*[:=]?\s*([^\s,.\[\]<>]{1,10})',
        r'▶\s*([^\s]{2,10})',
        r'☞\s*([^\s]{2,10})'
    ]

    for p in patterns:
        m = re.search(p, body)
        if m:
            ans = m.group(len(m.groups()))
            if ans not in bad_words:
                return ans

    return None


def crawl():
    headers = {'User-Agent': 'Mozilla/5.0'}

    targets = [
        {"url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
        {"url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"}
    ]

    include = ["토스","네이버","카카오","KB","신한","하나","페이","퀴즈","적립"]
    results = []

    for t in targets:
        try:
            res = requests.get(t['url'], headers=headers, timeout=10)
            if "ppomppu" in t['url']:
                res.encoding = 'euc-kr'

            soup = BeautifulSoup(res.text, 'html.parser')

            for a in soup.select('a'):
                title = clean_text(a.get_text())
                href = a.get('href','')

                if not title or len(title) < 6:
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

                    body = clean_text(ps.get_text())[:2000]

                    ans = extract_answer(title, body)

                    if ans:
                        info = f"[정답: {ans}]"
                    else:
                        info = "[확인필요]"

                except:
                    info = "[지연]"

                title_cut = title[:40]
                results.append(f"• {title_cut} {info}")

                if len(results) >= 25:
                    return results

        except:
            continue

    return results


def upload(text):
    print("📡 업로드 시작")

    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
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
        print("결과:", r.status_code)
        print(r.text)

    except Exception as e:
        print("업로드 실패:", e)


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
        text += "⏳ 정보 수집 중..."

    upload(text)


if __name__ == "__main__":
    run()
