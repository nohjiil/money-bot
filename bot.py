import os
from datetime import datetime
import pytz
from github import Github # pip install PyGithub 필요

# --- 환경 변수 설정 ---
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USER_ID = "nohjiil"
REPO_NAME = "money-bot"

# 1. 크롤링 함수들 (이전과 동일)
def get_toss_info():
    return "✅ [토스] 행운퀴즈 정답: 1234\n✅ [토스] 만보기 친구 링크: https://toss.im/..."

def get_naver_info():
    return "✅ [네이버] 쇼핑라이브 10원 링크: https://...\n✅ [네이버] 클릭 적립 링크: https://..."

def get_kakao_info():
    return "✅ [카카오] 카카오페이 퀴즈 정답: O"

def get_kb_info():
    return "✅ [KB] Pay 오늘의 퀴즈 정답: 포인세티아"

def get_shinhan_info():
    return "✅ [신한] 쏠야구 퀴즈 정답: 1번\n✅ [신한] 플레이 퀴즈팡팡 정답: X"

def get_hana_info():
    return "✅ [하나] 원큐 환전지갑 퀴즈 정답: 3번"

# 2. 텍스트 생성
def generate_content():
    korea_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(korea_tz).strftime('%Y년 %m월 %d일 %H:%M:%S')
    
    content = f"⏰ 마지막 업데이트: {now}\n"
    content += "="*30 + "\n\n"
    content += "[오늘의 정답 및 포인트 링크]\n"
    content += get_toss_info() + "\n\n"
    content += get_naver_info() + "\n\n"
    content += get_kakao_info() + "\n\n"
    content += get_kb_info() + "\n\n"
    content += get_shinhan_info() + "\n\n"
    content += get_hana_info() + "\n\n"
    content += "="*30 + "\n"
    content += "💡 앱 버튼을 눌러 바로 이동하세요!"
    
    return content

# 3. 깃허브 레포지토리 업데이트 함수
def update_github_repo(content):
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN이 설정되지 않았습니다.")
        return

    try:
        # 깃허브 로그인 및 레포지토리 연결
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(f"{USER_ID}/{REPO_NAME}")
        
        file_path = "data.txt"
        commit_message = f"업데이트: 포인트 정보 갱신 ({datetime.now().strftime('%m/%d %H:%M')})"

        try:
            # 기존 파일이 있는지 확인
            contents = repo.get_contents(file_path)
            # 파일이 있으면 업데이트 (Update)
            repo.update_file(contents.path, commit_message, content, contents.sha)
            print("✅ 깃허브 data.txt 업데이트 성공!")
        except:
            # 파일이 없으면 새로 생성 (Create)
            repo.create_file(file_path, commit_message, content)
            print("✅ 깃허브 data.txt 새로 생성 성공!")

    except Exception as e:
        print(f"❌ 깃허브 업데이트 중 오류 발생: {e}")

if __name__ == "__main__":
    new_data = generate_content()
    update_github_repo(new_data)
