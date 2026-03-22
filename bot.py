import requests, base64, os, re, time
from bs4 import BeautifulSoup

# GitHub 설정
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"

def get_rich():
    # 1. 수집 대상 설정
    targets = [
        {"name": "뽐뿌", "url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
        {"name": "클리앙", "url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"}
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # 🚀 사장님 맞춤 메이저 앱 (잡상인 차단)
    include_kws = ["토스", "네이버", "카카오", "KB", "국민", "신한", "쏠", "하나", "원큐", "스타뱅킹", "플레이"]
    
    # 🚀 [차단] 옥션, 이후동행, 지마켓 등 사장님 스트레스 요인 완벽 차단
    exclude_kws = ["모니모", "옥션", "비트버니", "핫딜", "출석", "만보기", "쇼핑", "이후동행", "동행퀴즈", "지마켓", "AI 키워", "키워드"]
    
    # 쓰레기 정답 필터
    forbidden = ["정보", "확인", "공유", "이벤트", "보기", "링크", "가기", "스크랩", "-", "ㅡ", "ㄱ", "ㄴ", "주"]
    
    found = []
    for target in targets:
        try:
            res = requests.get(target['url'], headers=headers, timeout=10)
            if "ppomppu" in target['url']: res.encoding = 'euc-kr'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            for a in soup.select('a'):
                txt = a.get_text().strip()
                href = a.get('href', '')
                
                # 1단계: 제목에서 메이저 앱만 필터링
                if any(k in txt for k in include_kws) and not any(e in txt for e in exclude_kws):
                    if len(txt) > 5 and href:
                        full_url = href if href.startswith('http') else target['base'] + href
                        info = ""
                        
                        # 2단계 [입단속]: 제목에 '퀴즈' 단어가 있을 때만 본문 '무제한 추적' 시작
                        if any(k in txt for k in ["퀴즈", "정답", "쏠", "하나", "원큐", "OX", "챌린지"]):
                            try:
                                time.sleep(1.0) # 서버 차단 방지 (여유 있게)
                                p_res = requests.get(full_url, headers=headers, timeout=7)
                                if "ppomppu" in full_url: p_res.encoding = 'euc-kr'
                                body = BeautifulSoup(p_res.text, 'html.parser').get_text()
                                
                                # 공백/엔터 모두 한 칸 공백으로 통합
                                body_clean = re.sub(r'\s+', ' ', body)
                                
                                # 🚀 [필살기] 정답 단어 뒤에 뭐가 있든 무시하고 끝까지 뒤집니다.
                                # .*? (가장 가까운 알맹이까지 점프) + ([^\s...]{1,12}) (공백 전까지 12자 낚시)
                                match = re.search(r'(정답|답|정답은|답은).*?[:=]?\s*([^\r\n\t\s,.<>]{1,12})', body_clean, re.DOTALL)
                                
                                if not match:
                                    # 괄호 수색 (HANA, 160경기 등 대응)
                                    match = re.search(r'\((\w{1,12})\)', body_clean)

                                if match:
                                    ans_val = (match.group(2) if len(match.groups()) > 1 else match.group(1)).strip()
                                    
                                    # 🚀 [OX 정밀 수색] '오', '엑스' 한글 정답도 O, X로 변환
                                    if ans_val.upper() in ["O", "X"] or ans_val in ["오", "엑스"]:
                                        final_ans = "O" if ans_val == "오" else ("X" if ans_val == "엑스" else ans_val.upper())
                                        info = f" [정답: {final_ans}]"
                                    # 가짜 정답(금지어)이거나 너무 짧으면 확인필요
                                    elif any(f in ans_val for f in forbidden) or len(ans_val) < 2:
                                        info = " [확인필요]"
                                    else:
                                        info = f" [정답: {ans_val}]"
                                else:
                                    info = " [확인필요]"
                            except:
                                info = " [연결지연]"
                        
                        # 🚀 제목에 퀴즈 단어 없으면 info는 "" 상태 -> 제목만 깔끔하게 출력 (확인필요 안 뜸!)
                        clean_t = txt.split('\n')[0][:25]
                        found.append(f"• {clean_t}{info}")
                        if len(found) >= 30: break
            if len(found) >= 30: break
        except: continue

    # 최종 텍스트 생성
    final_text = "✅ 실시간 포인트 정보 (정답/적립):<br><br>" + "<br>".join(found) if found else "⏳ 업데이트 중..."
    
    # GitHub 업로드 로직
    url = f"https://api.github.com/repos/{USER_ID}/{REPO_NAME}/contents/data.txt"
    h = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        g = requests.get(url, headers=h)
        sha = g.json().get('sha') if g.status_code == 200 else None
        content = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
        requests.put(url, json={"message": "final intelligence vacuum update", "content": content, "sha": sha} if sha else {"message": "init", "content": content}, headers=h)
    except: pass

if __name__ == "__main__":
    get_rich()
