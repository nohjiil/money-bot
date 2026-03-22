import requests, base64, os, re, hashlib
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from collections import Counter

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"
CACHE_FILE = "cache.txt"

# ---------------------------
# 정답 추출 (사장님 코드 보강 버전)
# ---------------------------
def extract_answer(txt, body):
    # 🚀 1. 입단속: 제목에 핵심 키워드가 없으면 본문 보지도 않음
    if not any(k in txt for k in ["퀴즈", "정답", "쏠", "하나", "원큐", "OX", "챌린지", "KB"]):
        return None

    # 🚀 2. 전처리: 엔터(줄바꿈)를 공백으로 바꿔서 거리 무력화
    body = body.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    
    # 🚀 3. 정답 낚시 (가장 확률 높은 패턴부터)
    # 패턴: '정답' 혹은 '답' 뒤에 나오는 1~12글자 (특수문자 제외)
    match = re.search(r'(정답|답|정답은|답은)\s*[:=]?\s*([^\s,.<>]{1,12})', body)
    if match:
        ans = match.group(2).strip()
        # 한 글자라도 O, X면 인정, 그 외엔 2글자 이상만 인정 (날짜 오인 방지)
        if len(ans) >= 2 or ans.upper() in ["O", "X"]:
            return ans

    # 🚀 4. 괄호 뒤지기 (HANA, 160경기 등)
    match = re.search(r'\((\w{1,12})\)', body)
    if match:
        return match.group(1).strip()

    return None

def get_clean_key(txt):
    return re.sub(r'[^\w가-힣]', '', txt)[:15]

def load_cache():
    try:
        with open(CACHE_FILE, "r") as f: return set(f.read().splitlines())
    except: return set()

def save_cache(cache):
    with open(CACHE_FILE, "w") as f: f.write("\n".join(list(cache)[-500:]))

def process_link(txt, full_url, headers, cache_set):
    key = hashlib.md5(full_url.encode()).hexdigest()
    if key in cache_set: return None
    try:
        res = requests.get(full_url, headers=headers, timeout=5)
        if "ppomppu" in full_url: res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        for s in soup(['script', 'style']): s.decompose()
        ans_val = extract_answer(txt, soup.get_text())
        if ans_val: return (get_clean_key(txt), ans_val, txt, key)
    except: return None

def get_rich():
    targets = [
        {"url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
        {"url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"}
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    include_kws = ["토스", "네이버", "카카오", "KB", "국민", "신한", "쏠", "퀴즈", "정답", "하나", "원큐"]
    
    # 🚀 [사장님 특별 지시] 차단 목록 강화
    exclude_kws = [
        "모니모", "옥션", "비트버니", "핫딜", "출석", "만보기", "쇼핑", 
        "AI 키워", "키워드", "이후동행", "동행퀴즈", "지마켓"
    ]

    cache = load_cache()
    tasks = []

    for target in targets:
        try:
            res = requests.get(target['url'], headers=headers, timeout=10)
            if "ppomppu" in target['url']: res.encoding = 'euc-kr'
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.select('a'):
                txt = a.get_text().strip()
                # 🚀 제외 키워드가 하나라도 있으면 아예 무시
                if any(k in txt for k in include_kws) and not any(e in txt for e in exclude_kws):
                    href = a.get('href', '')
                    if len(txt) > 5 and href:
                        tasks.append((txt, href if href.startswith('http') else target['base'] + href))
        except: continue

    answer_pool = {}
    new_keys = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda x: process_link(x[0], x[1], headers, cache), tasks))

    for r in results:
        if r:
            group_key, ans, full_txt, link_key = r
            if group_key not in answer_pool:
                answer_pool[group_key] = {"answers": [], "title": full_txt}
            answer_pool[group_key]["answers"].append(ans)
            new_keys.append(link_key)

    found = []
    for k, v in answer_pool.items():
        counter = Counter(v["answers"])
        best_ans, count = counter.most_common(1)[0]
        mark = "✔" if count >= 2 else "?"
        # 제목 앞머리만 깔끔하게 출력
        clean_t = v["title"].replace("[뽐뿌]", "").replace("[클리앙]", "").strip()[:20]
        found.append(f"• {clean_t} [정답: {best_ans} {mark}]")

    for nk in new_keys: cache.add(nk)
    save_cache(cache)
    
    final_text = "✅ 실시간 포인트 정보 (정답/적립):<br><br>" + "<br>".join(found) if found else "⏳ 새로운 정답을 찾는 중..."
    
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"
    h = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        g = requests.get(url, headers=h)
        sha = g.json().get('sha') if g.status_code == 200 else None
        content = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
        requests.put(url, json={"message": "clean-up & answer fix", "content": content, "sha": sha} if sha else {"message": "init", "content": content}, headers=h)
    except: pass

if __name__ == "__main__":
    get_rich()
