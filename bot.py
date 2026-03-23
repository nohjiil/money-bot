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
    exclude_kws = ["모니모", "옥션", "비트버니", "핫딜", "출석", "만보기", "쇼핑", "지마켓", "AI 키워", "키워드"]
    forbidden = ["정보", "확인", "공유", "이벤트", "보기", "링크", "가기", "스크랩", "-", "ㅡ", "ㄱ", "ㄴ", "주"]
    
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
                        
                        if any(k in title_txt for k in ["퀴즈", "정답", "쏠", "하나", "원큐", "OX", "챌린지"]):
                            try:
                                time.sleep(1.2) # 지연 방지
                                p_res = requests.get(full_url, headers=headers, timeout=7)
                                if "ppomppu" in full_url: p_res.encoding = 'euc-kr'
                                
                                p_soup = BeautifulSoup(p_res.text, 'html.parser')
                                for s in p_soup(['script', 'style', 'img', 'iframe']): s.decompose()
                                body_raw = p_soup.get_text()
                                
                                # 🚀 [필터 1] 광고/추신 절단 및 텍스트 정제
                                body_clean = body_raw.split("PS")[0].split("추신")[0].split("참고")[0].split("이벤트도")[0]
                                body_clean = re.sub(r'\s+', ' ', body_clean).strip()

                                # 🚀 [보완] 정답 못 찾을 경우를 대비해 본문 앞 40자 미리 따두기
                                preview = body_clean[:40].replace("'", "").replace('"', "")

                                # 🚀 [필터 2] 정밀 낚시
                                match = re.search(r'(정답|답|정답은|답은)\s*[:=]?\s*([^\s,.<>]{1,15})', body_clean)
                                
                                if not match:
                                    match = re.search(r'\((\w{1,15})\)', body_clean)

                                if match:
                                    ans_val = (match.group(2) if len(match.groups()) > 1 else match.group(1)).strip()
                                    
                                    # 제목에 있는 단어(황금열매 등)는 가짜로 판정
                                    if ans_val in title_txt and len(ans_val) > 1:
                                        info = f" [미리보기: {preview}...]"
                                    elif ans_val.upper() in ["O", "X"] or ans_val in ["오", "엑스"]:
                                        final_ans = "O" if ans_val == "오" else ("X" if ans_val == "엑스" else ans_val.upper())
                                        info = f" [정답: {final_ans}]"
                                    elif any(f in ans_val for f in forbidden) or len(ans_val) < 2:
                                        info = f" [미리보기: {preview}...]"
                                    else:
                                        info = f" [정답: {ans_val}]"
                                else:
                                    # 🚀 정답 못 찾으면 본문 보여주기
                                    info = f" [미리보기: {preview}...]"
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
        requests.put(url, json={"message": "full featured bot update", "content": content, "sha": sha} if sha else {"message": "init", "content": content}, headers=h)
    except: pass

if __name__ == "__main__":
    get_rich()
