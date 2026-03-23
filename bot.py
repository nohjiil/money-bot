import requests, base64, os, re, time
from bs4 import BeautifulSoup
from datetime import datetime

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"

def get_rich():
    targets = [
        {"url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
        {"url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"}
    ]

    headers = {'User-Agent': 'Mozilla/5.0'}

    include_kws = ["토스", "네이버", "카카오", "KB", "국민", "신한", "하나"]
    exclude_kws = ["핫딜", "쇼핑", "지마켓"]

    found = []
    seen = set()

    for target in targets:
        try:
            res = requests.get(target['url'], headers=headers, timeout=10)
            if "ppomppu" in target['url']:
                res.encoding = 'euc-kr'

            soup = BeautifulSoup(res.text, 'html.parser')

            for a in soup.select('a'):
                title_txt = a.get_text().strip()
                href = a.get('href', '')

                if not any(k in title_txt for k in include_kws):
                    continue
                if any(e in title_txt for e in exclude_kws):
                    continue
                if len(title_txt) < 6:
                    continue

                if title_txt in seen:
                    continue
                seen.add(title_txt)

                full_url = href if href.startswith('http') else target['base'] + href

                ans = ""

                try:
                    time.sleep(0.7)
                    p_res = requests.get(full_url, headers=headers, timeout=7)
                    if "ppomppu" in full_url:
                        p_res.encoding = 'euc-kr'

                    p_soup = BeautifulSoup(p_res.text, 'html.parser')
                    body = p_soup.get_text()

                    # 정답 찾기
                    m = re.search(r'(정답|답)[^\w]?[:=]?\s*([^\s,.<>]{2,15})', body)
                    if m:
                        ans = m.group(2)

                except:
                    pass

                # 👉 미리보기 제거 / 정답만
                if ans:
                    text = f"• {title_txt} [정답: {ans}]"
                else:
                    text = f"• {title_txt}"

                found.append(text)

                if len(found) >= 25:
                    break

            if len(found) >= 25:
                break

        except:
            continue

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 👉 🔥 핵심 수정 (HTML 제거)
    final_text = "\n".join([
        f"📅 업데이트 시간: {now}",
        "",
        "✅ 실시간 포인트 정보 (정답/적립)",
        "----------------------------------",
        *found
    ])

    # GitHub 업로드
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None

        content = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')

        data = {
            "message": "clean update",
            "content": content
        }

        if sha:
            data["sha"] = sha

        requests.put(url, json=data, headers=headers)

    except Exception as e:
        print("업로드 실패:", e)


if __name__ == "__main__":
    print("🔥 실행됨")
    get_rich()
