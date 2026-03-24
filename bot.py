import requests
import base64
from datetime import datetime, timedelta
import os
import re
import time
from bs4 import BeautifulSoup

# ====================
# 설정
# ====================
REPO = "nohjiil/money-bot"
FILE_PATH = "data.txt"
BRANCH = "main"
TOKEN = os.environ.get("GITHUB_TOKEN")

# ====================
# 진짜 데이터 수집 엔진
# ====================
def get_real_data():
    targets = [
        {"name": "뽐뿌", "url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon", "base": "https://www.ppomppu.co.kr/zboard/"},
        {"name": "클리앙", "url": "https://www.clien.net/service/board/jirum", "base": "https://www.clien.net"}
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    include_kws = ["토스", "네이버", "카카오", "KB", "국민", "신한", "쏠", "하나", "원큐", "스타뱅킹", "플레이"]
    exclude_kws = ["모니모", "옥션", "비트버니", "핫딜", "출석", "만보기", "쇼핑", "지마켓", "AI 키워", "키워드"]

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

                        t_match = re.search(r'[-:]\s*([^\s]{2,10})$', title_txt)
                        if t_match:
                            cand = t_match.group(1).strip()
                            if cand not in ["정답", "퀴즈", "소진", "종료", "완료"]:
                                ans = cand

                        try:
                            time.sleep(1.0)
                            p_res = requests.get(full_url, headers=headers, timeout=7)
                            if "ppomppu" in full_url: p_res.encoding = 'euc-kr'
                            p_soup = BeautifulSoup(p_res.text, 'html.parser')
                            
                            for s in p_soup(['script', 'style', 'img', 'iframe']): s.decompose()

                            body_raw = p_soup.get_text()
                            body_c = re.sub(r'\s+', ' ', body_raw).strip()
                            
                            # 🚀 [물리적 강제 절단기] 꼴보기 싫은 메뉴판 글씨를 통째로 잘라버립니다!
                            if "뽐뿌핫딜 쇼핑" in body_c:
                                body_c = body_c.split("뽐뿌핫딜 쇼핑")[-1]
                            if "테마설정 톺아보기" in body_c:
                                body_c = body_c.split("테마설정 톺아보기")[-1]
                            
                            # 조회수, 추천수 같은 잡다한 정보도 한 번 더 날림
                            body_c = re.sub(r'.*?조회수\s*:\s*\d+.*?추천\s*\d+', '', body_c)

                            body_cut = body_c.split("PS")[0].split("추신")[0].split("참고")[0].split("하세요")[0]

                            if not ans or len(ans) < 2:
                                m = re.search(r'(정답|답|정답은|답은)\s*[:=]\s*([^\s,.<>]{1,15})', body_cut)
                                if m: 
                                    ans = m.group(2).strip()
                                else:
                                    m2 = re.search(r'([^\s,.<>]{2,15})\s*-\s*정답', body_cut)
                                    if m2: ans = m2.group(1).strip()

                            ans = ans.replace(")", "").replace("(", "").strip()
                            if ans in ["정답", "퀴즈", "소진", "하세요"]:
                                ans = ""

                            if ans and ans in title_txt and not title_txt.endswith(ans):
                                ans = "" 

                            if ans and len(ans) >= 2:
                                info = f" [정답: {ans}]"
                            else:
                                # 앞부분에 남은 특수기호 제거 후 진짜 알맹이만!
                                clean_preview = re.sub(r'^[^a-zA-Z0-9가-힣]+', '', body_cut).strip()
                                info = f" [미리보기: {clean_preview[:35]}...]"
                        except:
                            info = " [연결지연]"

                        clean_t = title_txt.split('\n')[0][:25]
                        found.append(f"• {clean_t}{info}")
                        if len(found) >= 30: break
            if len(found) >= 30: break
        except: continue
    return found

# ====================
# 실행 및 업로드
# ====================
items = get_real_data()

now_kst = datetime.utcnow() + timedelta(hours=9)
now_str = now_kst.strftime("%Y-%m-%d %H:%M")

header = f"🗓️ 업데이트 시간: {now_str} (한국시간)\n\n✅ 실시간 포인트 정보 (정답/적립)\n------------------------\n\n"
body = "<br>".join(items) if items else "⏳ 정보 수집 중..."
final_text = header + body

print("🔥 BOT 실행됨")

url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
h = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}

res = requests.get(url, headers=h)
sha = res.json().get("sha") if res.status_code == 200 else None

encoded = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
data = {"message": "fix: brutal menu slicer", "content": encoded, "branch": BRANCH}
if sha: data["sha"] = sha

res = requests.put(url, headers=h, json=data)
print("🚀 업로드 결과:", res.status_code)
