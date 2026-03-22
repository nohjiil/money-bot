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
    include_kws = ["토스", "네이버", "카카오", "KB", "국민", "신한", "쏠", "플레이", "퀴즈", "정답", "적립", "클릭"]
    exclude_kws = ["모니모", "옥션", "비트버니", "핫딜", "출석", "만보기", "쇼핑"]
    
    found = []
    for target in targets:
        try:
            res = requests.get(target['url'], headers=headers, timeout=10)
            if "ppomppu" in target['url']: res.encoding = 'euc-kr'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            links = soup.select('a')
            for a in links:
                txt = a.get_text().strip()
                href = a.get('href', '')
                
                if any(k in txt for k in include_kws) and not any(e in txt for e in exclude_kws):
                    if len(txt) > 5 and href:
                        full_url = href if href.startswith('http') else target['base'] + href
                        
                        try:
                            p_res = requests.get(full_url, headers=headers, timeout=5)
                            if "ppomppu" in full_url: p_res.encoding = 'euc-kr'
                            p_soup = BeautifulSoup(p_res.text, 'html.parser')
                            body = p_soup.get_text()
                            
                            # 1. 정답 찾기
                            match = re.search(r'(정답|답|정답은)\s*[:=]?\s*([^\n\r\t\s,.<>]{1,15})', body)
                            
                            # 2. 광고/적립 링크 찾기 (네이버페이 등)
                            ad_link = re.search(r'https://ofw\.adison\.co/u/st/click/[^\s"\'<>]+|https://naver\.me/[^\s"\'<>]+', body)
                            
                            if match:
                                info = f" [정답: {match.group(2).strip()}]"
                            elif ad_link:
                                # 광고 링크가 있으면 클릭 가능한 형태로 변환
                                info = f' <a href="{ad_link.group(0)}" target="_blank">[적립링크 클릭]</a>'
                            else:
                                info = " [확인필요]"
                            
                            clean_t = txt.split('\n')[0][:25]
                            # HTML 링크가 포함될 수 있으므로 구조 변경
                            found.append(f"• {clean_t}{info}")
                        except:
                            found.append(f"• {txt[:25]} [연결지연]")
                        
                        if len(found) >= 20: break # 개수를 20개로 늘림
            if len(found) >= 20: break
        except: continue

    # 앱에서 링크가 작동하도록 HTML로 저장
    final_content = "✅ 실시간 포인트 정보 (정답/적립):<br><br>" + "<br>".join(found) if found else "⏳ 업데이트 중..."
    
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"
    h = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    g = requests.get(url, headers=h)
    sha = g.json().get('sha') if g.status_code == 200 else None
    content = base64.b64encode(final_content.encode('utf-8')).decode('utf-8')
    requests.put(url, json={"message": "final-upgrade", "content": content, "sha": sha} if sha else {"message": "init", "content": content}, headers=h)

if __name__ == "__main__":
    get_rich()
