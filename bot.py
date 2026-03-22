import requests, base64, os, re
from bs4 import BeautifulSoup

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"

def get_rich():
    targets = [
        {"name": "뽐뿌", "url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
        {"name": "클리앙", "url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"},
        {"name": "루리웹", "url": "https://bbs.ruliweb.com/market/board/1020", "base": ""}
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
            
            # 게시글 링크와 제목을 같이 수집
            items = soup.find_all('a')
            for item in items:
                txt = item.get_text().strip()
                link = item.get('href', '')
                
                if any(k in txt for k in include_kws) and not any(e in txt for e in exclude_kws):
                    if len(txt) > 5 and link:
                        # 풀 링크 만들기
                        full_link = link if link.startswith('http') else target['base'] + link
                        
                        # [핵심] 제목에 정답이 없으면 본문에서 살짝 엿보기 (간단 버전)
                        # 실제로는 제목만으로도 많은 정보가 확인되므로, 
                        # 여기서는 클릭 가능한 링크 형태로 만드는 데 집중합니다.
                        clean_txt = txt.split('\n')[0][:50]
                        entry = f'<a href="{full_link}" target="_blank">• {clean_txt}</a>'
                        if entry not in found: found.append(entry)
            
        except: continue

    # 앱에서 읽기 편하게 HTML 형태로 저장
    final_html = "✅ 실시간 엄선 정보 (클릭 시 이동):<br><br>" + "<br>".join(found[:15]) if found else "⏳ 업데이트 중..."
    
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"
    h = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    g = requests.get(url, headers=h)
    sha = g.json().get('sha') if g.status_code == 200 else None
    content = base64.b64encode(final_html.encode('utf-8')).decode('utf-8')
    requests.put(url, json={"message": "link-update", "content": content, "sha": sha} if sha else {"message": "init", "content": content}, headers=h)

if __name__ == "__main__":
    get_rich()
