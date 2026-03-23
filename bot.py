import requests, base64, os, re, time
from bs4 import BeautifulSoup

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"

def get_rich():
    targets = [
        {"name": "뽐뿌", "url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
        {"name": "클리앙", "url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"}
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    include_kws = ["토스", "네이버", "카카오", "KB", "국민", "신한", "쏠", "하나", "원큐", "스타뱅킹", "플레이"]
    exclude_kws = ["모니모", "비트버니", "핫딜", "출석", "만보기", "쇼핑", "지마켓", "AI 키워", "키워드"]
    
    found = []
    for target in targets:
        try:
            res = requests.get(target['url'], headers=headers, timeout=10)
            if "ppomppu" in target['url']: res.encoding = 'euc-kr'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            for a in soup.select('a'):
                title_txt = a.get_text().strip()
                href = a.get('href', '')
                
                if any(k in title_txt for k in include_kws) and not any(e in title_txt for e in exclude_kws):
                    if len(title_txt) > 5 and href:
                        full_url = href if href.startswith('http') else target['base'] + href
                        ans = ""
                        
                        # 🚀 [특수 낚시 1] 제목 끝에 '-' 뒤에 붙은 정답 낚기 (다이어리, 피톤치드 등)
                        t_match = re.search(r'-\s*([^\s]{2,10})$', title_txt)
                        if t_match: ans = t_match.group(1).strip()

                        try:
                            time.sleep(1.0)
                            p_res = requests.get(full_url, headers=headers, timeout=7)
                            if "ppomppu" in full_url: p_res.encoding = 'euc-kr'
                            p_soup = BeautifulSoup(p_res.text, 'html.parser')
                            for s in p_soup(['script', 'style', 'img', 'iframe']): s.decompose()
                            body_c = re.sub(r'\s+', ' ', p_soup.get_text()).strip()
                            body_cut = body_c.split("PS")[0].split("추신")[0]
                            
                            # 🚀 [특수 낚시 2] 본문에서 '정답 :' 패턴 찾기
                            if not ans:
                                m = re.search(r'(정답|답|정답은)\s*[:=]\s*([^\s,.<>]{1,15})', body_cut)
                                if m: ans = m.group(2).strip()
                            
                            if ans and len(ans) > 1:
                                info = f" [정답: {ans}]"
                            else:
                                info = f" [미리보기: {body_cut[:35]}...]"
                        except:
                            info = " [연결지연]"
                        
                        clean_t = title_txt.split('\n')[0][:25]
                        found.append(f"• {clean_t}{info}")
                        if len(found) >= 30: break
            if len(found) >= 30: break
        except: continue

    final_text = "✅ 실시간 포인트 정보 (정답/적립):<br><br>" + "<br>".join(found) if found else "⏳ 업데이트 중..."
    
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"
    h = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        g = requests.get(url, headers=h)
        sha = g.json().get('sha') if g.status_code == 200 else None
        content = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
        requests.put(url, json={"message": "fix: title-end answer detection", "content": content, "sha": sha} if sha else {"message": "init", "content": content}, headers=h)
    except: pass

if __name__ == "__main__":
    get_rich()
