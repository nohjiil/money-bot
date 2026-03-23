import requests, base64, os, re, time
from bs4 import BeautifulSoup
from datetime import datetime

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

USER_ID = "nohjiil"
REPO_NAME = "money-bot"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

INCLUDE_KWS = ["토스","네이버","카카오","KB","국민","신한","쏠","하나","원큐","스타뱅킹","플레이"]
EXCLUDE_KWS = ["모니모","옥션","비트버니","핫딜","출석","만보기","쇼핑","지마켓","AI 키워","키워드"]

TARGETS = [
    {"name": "뽐뿌", "url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
    {"name": "클리앙", "url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"}
]


def extract_answer(title, body):
    # 1. 제목 끝 정답
    m = re.search(r'[-\s:답]+([^\s]{2,10})$', title)
    if m:
        return m.group(1).strip()

    # 2. 본문 정답 패턴
    patterns = [
        r'(정답|답|정답은|답은)\s*[:=]\s*([^\s,.<>]{1,15})',
        r'([^\s,.<>]{2,15})\s*-\s*정답'
    ]

    for p in patterns:
        m = re.search(p, body)
        if m:
            return m.group(2 if len(m.groups()) > 1 else 1).strip()

    return None


def crawl():
    results = []

    for target in TARGETS:
        try:
            res = requests.get(target['url'], headers=HEADERS, timeout=10)
            if "ppomppu" in target['url']:
                res.encoding = 'euc-kr'

            soup = BeautifulSoup(res.text, 'html.parser')

            for a in soup.select('a'):
                title = a.get_text().strip()
                href = a.get('href', '')

                if not title or not href:
                    continue

                if not any(k in title for k in INCLUDE_KWS):
                    continue

                if any(e in title for e in EXCLUDE_KWS):
                    continue

                url = href if href.startswith('http') else target['base'] + href

                answer = None
                preview = ""

                try:
                    time.sleep(0.7)
                    p = requests.get(url, headers=HEADERS, timeout=7)
                    if "ppomppu" in url:
                        p.encoding = 'euc-kr'

                    ps = BeautifulSoup(p.text, 'html.parser')
                    for s in ps(['script','style','img','iframe']):
                        s.decompose()

                    body = re.sub(r'\s+', ' ', ps.get_text()).strip()
                    body_cut = body.split("PS")[0].split("추신")[0]

                    answer = extract_answer(title, body_cut)

                    if not answer:
                        preview = body_cut[:30]

                except:
                    preview = "연결지연"

                clean_title = title.split('\n')[0][:30]

                if answer:
                    line = f"• {clean_title} [정답: {answer}]"
                else:
                    line = f"• {clean_title} [확인필요]"

                results.append(line)

                if len(results) >= 25:
                    return results

        except:
            continue

    return results


def make_text(items):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not items:
        items = ["⏳ 정보 수집 중..."]

    text = f"""📅 업데이트 시간: {now}

✅ 실시간 포인트 정보 (정답/적립)
----------------------------------
""" + "\n".join(items)

    return text


def upload_github(text):
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
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

    res = requests.put(url, json=data, headers=headers)
    print("GitHub:", res.status_code)


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }

    res = requests.post(url, data=data)
    print("Telegram:", res.status_code)


def main():
    print("🔥 BOT 실행")

    items = crawl()
    text = make_text(items)

    upload_github(text)
    send_telegram(text)

    print("✅ 완료")


if __name__ == "__main__":
    main()
