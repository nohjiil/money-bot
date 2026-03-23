import requests, base64, os, re, time
from bs4 import BeautifulSoup

# GitHub 설정
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"

def get_rich():
    targets = [
        {"name": "뽐뿌", "url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
        {"name": "클리앙", "url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"}
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # 🚀 사장님 맞춤 앱 (잡상인 차단)
    include_kws = ["토스", "네이버", "카카오", "KB", "국민", "신한", "쏠", "하나", "원큐", "스타뱅킹", "플레이"]
    exclude_kws = ["모니모", "옥션", "비트버니", "핫딜", "출석", "만보기", "쇼핑", "이후동행", "동행퀴즈", "지마켓", "AI 키워", "키워드"]
    
    # 정답으로 인정 안 하는 쓰레기 단어들
    forbidden = ["정보", "확인", "공유", "이벤트", "보기", "링크", "가기", "스크랩", "-", "ㅡ", "ㄱ", "ㄴ", "주", "클릭"]
    
    found = []
    for target in targets:
        try:
            res = requests.get(target['url'], headers=headers, timeout=10)
            if "ppomppu" in target['url']: res.encoding = 'euc-kr'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            for a in soup.select('a'):
                title_txt = a.get_text().strip()
                href = a.get('href', '')
                
                # 1단계: 제목 필터링
                if any(k in title_txt for k in include_kws) and not any(e in title_txt for e in exclude_kws):
                    if len(title_txt) > 5 and href:
                        full_url = href if href.startswith('http') else target['base'] + href
                        info = ""
                        
                        # 2단계: 퀴즈 키워드가 있을 때만 본문 '정밀 수색'
                        if any(k in title_txt for k in ["퀴즈", "정답", "쏠", "하나", "원큐", "OX", "챌린지"]):
                            try:
                                time.sleep(1.2) # 서버 차단 방지 (넉넉하게)
                                p_res = requests.get(full_url, headers=headers, timeout=7)
                                if "ppomppu" in full_url: p_res.encoding = 'euc-kr'
                                
                                # 본문 텍스트만 추출 및 클리닝
                                p_soup = BeautifulSoup(p_res.text, 'html.parser')
                                for s in p_soup(['script', 'style', 'img', 'iframe']): s.decompose()
                                body_raw = p_soup.get_text()
                                
                                # 🚀 [필터 1] 광고/추신(PS) 이후는 과감히 절단!
                                body_clean = body_raw.split("PS")[0].split("추신")[0].split("참고")[0].split("이벤트도")[0]
                                body_clean = re.sub(r'\s+', ' ', body_clean) # 한 줄로 펴기

                                # 🚀 [필터 2] 정밀 정답 낚시 (제목에 있는 단어는 제외!)
                                # '정답' 뒤 15자 이내의 알맹이를 찾습니다.
                                match = re.search(r'(정답|답|정답은|답은)\s*[:=]?\s*([^\s,.<>]{1,15})', body_clean)
                                
                                if not match:
                                    # 괄호 수색 (HANA, 160경기 등 대응)
                                    match = re.search(r'\((\w{1,15})\)', body_clean)

                                if match:
                                    ans_val = (match.group(2) if len(match.groups()) > 1 else match.group(1)).strip()
                                    
                                    # 🚀 [필터 3] 찾은 답이 제목에 포함된 '황금열매' 같은 녀석이면 버림!
                                    if ans_val in title_txt and len(ans_val) > 1:
                                        # 제목에 없는 다른 패턴을 한 번 더 수색
                                        m2 = re.search(r'[:]\s*([^\s,.<>]{2,15})', body_clean)
                                        ans_val = m2.group(1).strip() if m2 else "확인필요"

                                    # OX 변환 및 최종 정리
                                    if ans_val.upper() in ["O", "X"] or ans_val in ["오", "엑스"]:
                                        final_ans = "O" if ans_val == "오" else ("X" if ans_val == "엑스" else ans_val.upper())
                                        info = f" [정답: {final_ans}]"
                                    elif any(f in ans_val for f in forbidden) or len(ans_val) < 2:
                                        info = " [확인필요]"
                                    else:
                                        info = f" [정답: {ans_val}]"
                                else:
                                    info = " [확인필요]"
                            except:
                                info = " [연결지연]"
                        
                        # 최종 리스트 추가
                        clean_t = title_txt.split('\n')[0][:25]
                        found.append(f"• {clean_t}{info}")
                        if len(found) >= 30: break
            if len(found) >= 30: break
        except: continue

    final_text = "✅ 실시간 포인트 정보 (정답/적립):<br><br>" + "<br>".join(found) if found else "⏳ 업데이트 중..."
    
    # GitHub 업로드
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"
    h = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        g = requests.get(url, headers=h)
        sha = g.json().get('sha') if g.status_code == 200 else None
        content = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
        requests.put(url, json={"message": "fix: title filter & ad removal", "content": content, "sha": sha} if sha else {"message": "init", "content": content}, headers=h)
    except: pass

if __name__ == "__main__":
    get_rich()
