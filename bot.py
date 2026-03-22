import requests, base64, os, re
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
    include_kws = ["토스", "네이버", "카카오", "KB", "국민", "신한", "쏠", "플레이", "퀴즈", "정답"]
    exclude_kws = ["모니모", "옥션", "비트버니", "핫딜", "출석", "만보기", "쇼핑"]
    
    found = []
    for target in targets:
        try:
            res = requests.get(target['url'], headers=headers, timeout=10)
            if "ppomppu" in target['url']: res.encoding = 'euc-kr'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 게시글 링크들 수집 (뽐뿌/클리앙 구조에 맞춤)
            links = soup.select('a')
            for a in links:
                txt = a.get_text().strip()
                href = a.get('href', '')
                
                if any(k in txt for k in include_kws) and not any(e in txt for e in exclude_kws):
                    if len(txt) > 5 and href:
                        full_url = href if href.startswith('http') else target['base'] + href
                        
                        try:
                            # [핵심] 글 안으로 깊숙이 들어갑니다
                            p_res = requests.get(full_url, headers=headers, timeout=5)
                            if "ppomppu" in full_url: p_res.encoding = 'euc-kr'
                            p_soup = BeautifulSoup(p_res.text, 'html.parser')
                            body = p_soup.get_text()
                            
                            # 정답을 찾는 3단계 정규식 (더 강력해짐)
                            # 1. '정답 : 사과' 형태 찾기
                            match = re.search(r'(정답|답|정답은)\s*[:=]?\s*([^\n\r\t\s,.<>]{1,15})', body)
                            # 2. '퀴즈 정답은 123' 형태 찾기
                            if not match:
                                match = re.search(r'정답\s+([^\n\r\t\s,.<>]{1,10})', body)
                            
                            ans = f" [정답: {match.group(2).strip()}]" if match else " [정답: 글 확인필요]"
                            
                            clean_t = txt.split('\n')[0][:30]
                            found.append(f"• {clean_t}{ans}")
                        except:
                            found.append(f"• {txt[:30]} [연결지연]")
                        
                        if len(found) >= 15: break
            if len(found) >= 15: break
        except: continue

    final_text = "✅ 실시간 엄선 정보 (정답 포함):\n\n" + "\n".join(found) if found else "⏳ 업데이트 중..."
    
    # 데이터 저장
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"
    h = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    g = requests.get(url, headers=h)
    sha = g.json().get('sha') if g.status_code == 200 else None
    content = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    requests.put(url, json={"message": "ans-extract-update", "content": content, "sha": sha} if sha else {"message": "init", "content": content}, headers=h)

if __name__ == "__main__":
    get_rich()
