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
    include_kws = ["토스", "네이버", "카카오", "KB", "국민", "신한", "쏠", "플레이", "퀴즈", "정답", "하나", "원큐"]
    exclude_kws = ["모니모", "옥션", "비트버니", "핫딜", "출석", "만보기", "쇼핑"]
    forbidden = ["뽐뿌", "클리앙", "정보", "확인", "공유", "이벤트", "보기", "링크", "가기", "스크랩", "-", "ㅡ", "ㄱ", "ㄴ", "주"]
    
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
                        info = ""
                        
                        # 🚀 [사장님 특급 지시] 제목에 아래 키워드가 하나라도 있어야 '정답 수사' 시작
                        if any(k in txt for k in ["퀴즈", "정답", "쏠", "하나", "원큐", "OX", "챌린지"]):
                            try:
                                p_res = requests.get(full_url, headers=headers, timeout=5)
                                if "ppomppu" in full_url: p_res.encoding = 'euc-kr'
                                body = BeautifulSoup(p_res.text, 'html.parser').get_text()
                                
                                # 줄바꿈 무시하고 30자 이내 정답 탐색
                                match = re.search(r'(정답|답|정답은|답은).{0,30}?\s*[:=]?\s*([^\r\n\t\s,.<>]{1,12})', body, re.DOTALL)
                                if not match:
                                    match = re.search(r'\((\w{1,12})\)', body)

                                if match:
                                    ans_val = (match.group(2) if len(match.groups()) > 1 else match.group(1)).strip()
                                    if (ans_val in forbidden or len(ans_val) < 1) and ans_val.upper() not in ["O", "X"]:
                                        info = " [확인필요]"
                                    else:
                                        info = f" [정답: {ans_val}]"
                                else:
                                    info = " [확인필요]"
                            except:
                                info = " [연결지연]"
                        
                        # 🚀 '퀴즈' 단어 없으면 info는 "" 상태 그대로 -> 깔끔하게 제목만 나옴
                        clean_t = txt.split('\n')[0][:25]
                        found.append(f"• {clean_t}{info}")
                        if len(found) >= 20: break
            if len(found) >= 20: break
        except: continue

    final_text = "✅ 실시간 포인트 정보 (정답/적립):<br><br>" + "<br>".join(found) if found else "⏳ 업데이트 중..."
    
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"
    h = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    g = requests.get(url, headers=h)
    sha = g.json().get('sha') if g.status_code == 200 else None
    content = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    requests.put(url, json={"message": "strict-title-check", "content": content, "sha": sha} if sha else {"message": "init", "content": content}, headers=h)

if __name__ == "__main__":
    get_rich()
