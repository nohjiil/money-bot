import requests, base64, os, re, hashlib
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from collections import Counter

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"
CACHE_FILE = "cache.txt"

# 🚀 [정밀 수술] 정답 추출 로직
def extract_answer(txt, body):
    # 1. 입단속: 제목에 핵심 키워드 없으면 무시
    if not any(k in txt for k in ["퀴즈", "정답", "쏠", "하나", "원큐", "OX", "챌린지", "KB"]):
        return None
    
    # 2. 본문 정규화 (엔터/탭 제거)
    body_clean = body.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    
    # 3. 정답 낚시 (정답: 뒤에 오는 1~12글자만 타이트하게 낚음)
    # 사장님, 여기서 12자 이내로 제한해서 '매주' 같은 단어가 섞이는걸 막았습니다.
    m = re.search(r'(정답|답|정답은|답은)\s*[:=]?\s*([^\s,.<>]{1,12})', body_clean)
    if m:
        ans = m.group(2).strip()
        # O, X는 한글자 허용, 나머지는 2글자 이상 (날짜 오인 방지)
        if len(ans) >= 2 or ans.upper() in ["O", "X"]:
            return ans

    # 4. 괄호 수색 (하나원큐 HANA 등 대비)
    m = re.search(r'\((\w{1,12})\)', body_clean)
    if m: return m.group(1).strip()
    
    return None

def get_clean_key(txt):
    # 제목에서 특수문자 빼고 핵심 15자만 추출 (그룹화용)
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    include_kws = ["토스", "네이버", "카카오", "KB", "국민", "신한", "쏠", "퀴즈", "정답", "하나", "원큐"]
    # 🚀 [사장님 지시] 옥션, 이후동행 완벽 차단 목록
    exclude_kws = ["모니모", "옥션", "비트버니", "핫딜", "출석", "만보기", "쇼핑", "AI 키워", "키워드", "이후동행", "동행퀴즈", "지마켓", "옥션매일"]

    cache = load_cache()
    tasks = []

    for target in targets:
        try:
            res = requests.get(target['url'], headers=headers, timeout=10)
            if "ppomppu" in target['url']: res.encoding = 'euc-kr'
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.select('a'):
                txt = a.get_text().strip()
                # 🚀 제외 키워드가 있으면 아예 클릭도 안 함
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
        # 다수결 체크 표시 (선택사항)
        mark = "✔" if count >= 2 else ""
        clean_t = v["title"].replace("[뽐뿌]", "").replace("[클리앙]", "").strip()[:22]
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
        requests.put(url, json={"message": "clean-up & 정밀수사", "content": content, "sha": sha} if sha else {"message": "init", "content": content}, headers=h)
    except: pass

if __name__ == "__main__":
    get_rich()
