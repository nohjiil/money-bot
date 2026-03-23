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
                        info = ""
                        
                        try:
                            time.sleep(1.0)
                            p_res = requests.get(full_url, headers=headers, timeout=7)
                            if "ppomppu" in full_url: p_res.encoding = 'euc-kr'
                            p_soup = BeautifulSoup(p_res.text, 'html.parser')
                            for s in p_soup(['script', 'style', 'img', 'iframe']): s.decompose()
                            body = p_soup.get_text()
                            
                            # 🚀 [수리] 광고 절단 및 텍스트 청소
                            body_c = body.split("PS")[0].split("추신")[0].split("참고")[0]
                            body_c = re.sub(r'\s+', ' ', body_c).strip()
                            
                            # 🚀 [핵심] 정답을 더 공격적으로 낚는 낚시바늘들
                            # 1순위: '정답 : 단어' (신세계면세점 등)
                            m1 = re.search(r'(정답|답|정답은|답은)\s*[:=]\s*([^\s,.<>]{1,15})', body_c)
                            # 2순위: '숫자번 단어' (3번 신세계 등)
                            m2 = re.search(r'(\d번)\s*([^\s,.<>]{1,15})', body_c)
                            # 3순위: 괄호 안의 단어 (HANA 등)
                            m3 = re.search(r'\((\w{1,15})\)', body_c)

                            ans = ""
                            if m1: ans = m1.group(2).strip()
                            elif m2: ans = f"{m2.group(1)} {m2.group(2).strip()}"
                            elif m3: ans = m3.group(1).strip()

                            # 제목 낚시(황금열매 등) 차단 로직
                            if ans and ans in title_txt and len(ans) > 1: ans = ""

                            if ans and len(ans) > 1:
                                info = f" [정답: {ans}]"
                            else:
                                # 정답 못 찾으면 그때만 미리보기!
                                info = f" [미리보기: {body_c[:35]}...]"
                        except:
                            info = " [확인필요]"
                        
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
        requests.put(url, json={"message": "fix: aggressive answer extraction", "content": content, "sha": sha} if sha else {"message": "init", "content": content}, headers=h)
    except: pass

if __name__ == "__main__":
    get_rich()
