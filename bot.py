import requests, base64, os, re, time
from bs4 import BeautifulSoup
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USER_ID = "nohjiil"
REPO_NAME = "money-bot"
FILE_PATH = "data.txt"

API_URL = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/{FILE_PATH}"

HEADERS = {'User-Agent': 'Mozilla/5.0'}

# ✅ 키워드 필터 (필요하면 추가)
INCLUDE = ["토스", "네이버", "카카오", "KB", "신한", "하나"]
EXCLUDE = ["핫딜", "쇼핑", "지마켓", "옥션", "쿠팡"]


def crawl():
    sources = [
        {"url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
        {"url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"}
    ]

    results = []
    seen = set()

    for s in sources:
        try:
            res = requests.get(s["url"], headers=HEADERS, timeout=10)

            if "ppomppu" in s["url"]:
                res.encoding = "euc-kr"

            soup = BeautifulSoup(res.text, "html.parser")

            for a in soup.select("a"):
                title = a.get_text().strip()
                href = a.get("href", "")

                if not title or len(title) < 6:
                    continue

                if not any(k in title for k in INCLUDE):
                    continue

                if any(e in title for e in EXCLUDE):
                    continue

                if title in seen:
                    continue

                seen.add(title)

                link = href if href.startswith("http") else s["base"] + href

                answer = ""

                # 👉 상세 페이지 들어가서 정답 찾기
                try:
                    time.sleep(0.7)
                    r = requests.get(link, headers=HEADERS, timeout=7)

                    if "ppomppu" in link:
                        r.encoding = "euc-kr"

                    text = BeautifulSoup(r.text, "html.parser").get_text()

                    m = re.search(r'(정답|답)[^\w]?[:=]?\s*([^\s,.<>]{2,15})', text)
                    if m:
                        answer = m.group(2)

                except:
                    pass

                # 👉 출력 형태 (미리보기 없음)
                if answer:
                    results.append(f"• {title} [정답: {answer}]")
                else:
                    results.append(f"• {title}")

                if len(results) >= 25:
                    break

            if len(results) >= 25:
                break

        except:
            continue

    return results


def make_text(items):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return "\n".join([
        f"📅 업데이트 시간: {now}",
        "",
        "✅ 실시간 포인트 정보 (정답/적립)",
        "----------------------------------",
        *items if items else ["⏳ 정보 수집 중..."]
    ])


def upload(text):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    res = requests.get(API_URL, headers=headers)
    sha = res.json()["sha"] if res.status_code == 200 else None

    content = base64.b64encode(text.encode("utf-8")).decode("utf-8")

    data = {
        "message": "auto update",
        "content": content
    }

    if sha:
        data["sha"] = sha

    res = requests.put(API_URL, headers=headers, json=data)

    print("업로드 결과:", res.status_code)


if __name__ == "__main__":
    print("🚀 크롤링 시작")

    items = crawl()
    text = make_text(items)

    upload(text)

    print("✅ 완료")
