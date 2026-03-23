import requests, base64, os, re, time
from bs4 import BeautifulSoup
from datetime import datetime

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

USER_ID = "nohjiil"
REPO_NAME = "money-bot"

HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

INCLUDE_KWS = ["토스","네이버","카카오","KB","국민","신한","쏠","하나","원큐","스타뱅킹","플레이"]
EXCLUDE_KWS = ["모니모","옥션","비트버니","핫딜","출석","만보기","쇼핑","지마켓","AI 키워","키워드"]

TARGETS = [
    {"url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
    {"url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"}
]

# ❌ 쓰레기 정답 필터
BAD_ANS = ["정답", "정보", "확인", "받으세요", "이벤트", "팀플전"]

def is_valid_answer(ans):
    if not ans:
        return False
    if ans in BAD_ANS:
        return False
    if len(ans) < 2:
        return False
    if not re.match(r'^[가-힣A-Za-z0-9]{2,10}$', ans):
        return False
    return True


def extract_answer(title, text):
    # 제목에서 찾기
    m = re.search(r'[-: ]([가-힣A-Za-z0-9]{2,10})$', title)
    if m:
        return m.group(1)

    # 본문 + 댓글에서 찾기
    patterns = [
        r'(정답|답|정답은|답은)\s*[:=]\s*([가-힣A-Za-z0-9]{2,10})',
        r'([가-힣A-Za-z0-9]{2,10})\s*-\s*정답'
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(2 if len(m.groups()) > 1 else 1)

    return None


# 🔥 댓글 추출 (핵심)
def extract_comments(soup):
    comments = []
    for c in soup.select('.comment, .reply, .cmt_content, td.comment'):
        t = c.get_text().strip()
        if t:
            comments.append(t)
    return " ".join(comments)


def crawl():
    results = []

    for t in TARGETS:
        try:
            r = requests.get(t['url'], headers=HEADERS, timeout=10)
            if "ppomppu" in t['url']:
                r.encoding = 'euc-kr'

            soup = BeautifulSoup(r.text, 'html.parser')

            for a in soup.select('a'):
                title = a.get_text().strip()
                href = a.get('href', '')

                if not title or not href:
                    continue

                if not any(k in title for k in INCLUDE_KWS):
                    continue

                if any(e in title for e in EXCLUDE_KWS):
                    continue

                url = href if href.startswith('http') else t['base'] + href

                try:
                    time.sleep(0.7)
                    p = requests.get(url, headers=HEADERS, timeout=7)
                    if "ppomppu" in url:
                        p.encoding = 'euc-kr'

                    ps = BeautifulSoup(p.text, 'html.parser')

                    for s in ps(['script','style','img','iframe']):
                        s.decompose()

                    body = re.sub(r'\s+', ' ', ps.get_text()).strip()

                    # 🔥 댓글 포함
                    comments = extract_comments(ps)
                    full_text = body + " " + comments

                    answer = extract_answer(title, full_text)

                    clean_title = title[:30]

                    # 🔥 필터 적용
                    if is_valid_answer(answer):
                        results.append(f"• {clean_title} [정답: {answer}]")

                    if len(results) >= 20:
                        return results

                except:
                    continue

        except:
            continue

    return results


def make_text(items):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not items:
        items = ["⏳ 정답 없음"]

    return f"""📅 업데이트 시간: {now}

✅ 실시간 포인트 정보 (정답/적립)
----------------------------------
""" + "\n".join(items)


def upload_github(text):
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None

    content = base64.b64encode(text.encode()).decode()

    data = {
        "message": "update",
        "content": content
    }

    if sha:
        data["sha"] = sha

    requests.put(url, json=data, headers=headers)


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }

    requests.post(url, data=data)


def main():
    print("🔥 실행")

    items = crawl()
    text = make_text(items)

    upload_github(text)
    send_telegram(text)

    print("✅ 완료")


if __name__ == "__main__":
    main()
