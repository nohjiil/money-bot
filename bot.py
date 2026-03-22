import requests, base64, os, re, hashlib
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from collections import Counter

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"

CACHE_FILE = "cache.txt"

# ---------------------------
# 앱 분류
# ---------------------------
def detect_app(txt):
    if "토스" in txt:
        return "toss"
    elif "신한" in txt or "쏠" in txt:
        return "shinhan"
    elif "카카오" in txt:
        return "kakao"
    elif "KB" in txt or "국민" in txt:
        return "kb"
    elif "하나" in txt:
        return "hana"
    return "etc"

# ---------------------------
# 정답 추출
# ---------------------------
def extract_answer(app, body):
    body = body.replace("\n", " ")

    if app == "shinhan":
        m = re.search(r'(정답|답).{0,50}?(\d{1,6})', body)
        if m:
            return m.group(2)

    elif app == "toss":
        m = re.search(r'(정답|답).{0,30}?[:=]?\s*([가-힣A-Za-z0-9]{1,10})', body)
        if m:
            return m.group(2)

    elif app == "kakao":
        m = re.search(r'(정답|답).{0,30}?[:=]?\s*([가-힣A-Za-z0-9]{1,15})', body)
        if m:
            return m.group(2)

    elif app in ["kb", "hana"]:
        m = re.search(r'(정답|답).{0,40}?[:=]?\s*([^\s,.<>]{1,12})', body)
        if m:
            return m.group(2)

    # fallback
    m = re.search(r'(정답|답).{0,50}?(\d{1,6})', body)
    if m:
        return m.group(2)

    m = re.search(r'\((\d{1,6}|\w{1,12})\)', body)
    if m:
        return m.group(1)

    return None

# ---------------------------
# 캐시
# ---------------------------
def load_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            return set(f.read().splitlines())
    except:
        return set()

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        f.write("\n".join(cache))

# ---------------------------
# 링크 처리
# ---------------------------
def process_link(txt, full_url, headers, cache):
    key = hashlib.md5(full_url.encode()).hexdigest()

    if key in cache:
        return None

    try:
        res = requests.get(full_url, headers=headers, timeout=5)
        if "ppomppu" in full_url:
            res.encoding = 'euc-kr'

        body = BeautifulSoup(res.text, 'html.parser').get_text()

        app = detect_app(txt)
        ans_val = extract_answer(app, body)

        cache.add(key)

        if ans_val:
            title_key = txt[:20]  # 👉 그룹 기준
            return (title_key, ans_val, txt)

    except:
        return None

# ---------------------------
# 메인
# ---------------------------
def get_rich():
    targets = [
        {"url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
        {"url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"}
    ]

    headers = {'User-Agent': 'Mozilla/5.0'}

    include_kws = ["토스", "네이버", "카카오", "KB", "국민", "신한", "쏠", "퀴즈", "정답", "하나"]
    exclude_kws = ["모니모", "옥션", "비트버니", "핫딜", "출석", "만보기", "쇼핑", "AI 키워", "키워드"]

    cache = load_cache()
    tasks = []

    # ---------------------------
    # 링크 수집
    # ---------------------------
    for target in targets:
        try:
            res = requests.get(target['url'], headers=headers, timeout=10)
            if "ppomppu" in target['url']:
                res.encoding = 'euc-kr'

            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.select('a')

            for a in links:
                txt = a.get_text().strip()
                href = a.get('href', '')

                if any(k in txt for k in include_kws) and not any(e in txt for e in exclude_kws):
                    if len(txt) > 5 and href:
                        full_url = href if href.startswith('http') else target['base'] + href

                        if any(k in txt for k in ["퀴즈", "정답", "OX"]):
                            tasks.append((txt, full_url))

        except:
            continue

    # ---------------------------
    # 병렬 처리
    # ---------------------------
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(
            lambda x: process_link(x[0], x[1], headers, cache),
            tasks
        )

    # ---------------------------
    # 다수결 정답 계산
    # ---------------------------
    answer_pool = {}

    for r in results:
        if not r:
            continue

        title_key, ans_val, original_txt = r

        if title_key not in answer_pool:
            answer_pool[title_key] = {"answers": [], "title": original_txt}

        answer_pool[title_key]["answers"].append(ans_val)

    # ---------------------------
    # 최종 결과 생성
    # ---------------------------
    found = []

    for k, v in answer_pool.items():
        counter = Counter(v["answers"])
        best_ans, count = counter.most_common(1)[0]

        if count >= 2:
            info = f" [정답: {best_ans} ✔]"
        else:
            info = f" [정답: {best_ans} ?]"

        clean_t = v["title"].split('\n')[0][:25]
        found.append(f"• {clean_t}{info}")

        if len(found) >= 20:
            break

    save_cache(cache)

    final_text = "✅ 실시간 포인트 정보 (정답/적립):<br><br>" + "<br>".join(found) if found else "⏳ 업데이트 중..."

    # ---------------------------
    # GitHub 업로드
    # ---------------------------
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"
    h = {"Authorization": f"token {GITHUB_TOKEN}"}

    g = requests.get(url, headers=h)
    sha = g.json().get('sha') if g.status_code == 200 else None

    content = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')

    requests.put(
        url,
        json={"message": "final bot", "content": content, "sha": sha} if sha else {"message": "init", "content": content},
        headers=h
    )


if __name__ == "__main__":
    get_rich()
