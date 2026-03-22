import requests, base64, os
from bs4 import BeautifulSoup

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"

def get_rich():
    targets = [
        {"name": "뽐뿌", "url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon"},
        {"name": "클리앙", "url": "https://www.clien.net/service/board/jirum"},
        {"name": "루리웹", "url": "https://bbs.ruliweb.com/market/board/1020"}
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    include_kws = ["토스", "네이버", "카카오", "KB", "국민", "신한", "쏠", "플레이", "퀴즈", "정답"]
    exclude_kws = ["모니모", "옥션", "비트버니", "핫딜", "출석", "만보기", "쇼핑"]
    
    found = []
    for target in targets:
        try:
            res = requests.get(target['url'], headers=headers, timeout=10)
            if "ppomppu" in target['url']: res.encoding = 'euc-kr'
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.find_all(['a', 'span', 'font']):
                txt = item.get_text().strip()
                if any(k in txt for k in include_kws) and not any(e in txt for e in exclude_kws):
                    if len(txt) > 5:
                        clean = txt.split('\n')[0][:50]
                        if clean not in found: found.append(clean)
        except: continue

    final_text = "✅ 실시간 엄선 정보:\n\n" + "\n".join([f"• {i}" for i in found[:15]]) if found else "⏳ 업데이트 중..."
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"
    h = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    g = requests.get(url, headers=h)
    sha = g.json().get('sha') if g.status_code == 200 else None
    content = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    requests.put(url, json={"message": "auto-update", "content": content, "sha": sha} if sha else {"message": "auto-init", "content": content}, headers=h)

if __name__ == "__main__":
    get_rich()
