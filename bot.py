import os
from datetime import datetime
import pytz # timezone 설정을 위해 필요 (pip install pytz)

# 1. 각 포인트 앱별 정보 수집 함수 (여기에 크롤링 코드 추가)
def get_toss_info():
    # TODO: 뽐뿌 재테크포럼 등에서 토스 만보기/행운퀴즈 링크 크롤링 (requests, BeautifulSoup 사용)
    # 현재는 예시 데이터입니다. HTML에서 "토스" 키워드를 카운트합니다.
    return "✅ [토스] 행운퀴즈 정답: 1234\n✅ [토스] 만보기 친구 링크: https://toss.im/..."

def get_naver_info():
    # 현재는 예시 데이터입니다. HTML에서 "네이버" 키워드를 카운트합니다.
    return "✅ [네이버] 쇼핑라이브 10원 링크: https://...\n✅ [네이버] 클릭 적립 링크: https://..."

def get_kakao_info():
    # HTML에서 "카카오" 키워드를 카운트합니다.
    return "✅ [카카오] 카카오페이 퀴즈 정답: O"

def get_kb_info():
    # HTML에서 "KB" 키워드를 카운트합니다.
    return "✅ [KB] Pay 오늘의 퀴즈 정답: 포인세티아"

def get_shinhan_info():
    # HTML에서 "신한" 키워드를 카운트합니다.
    return "✅ [신한] 쏠야구 퀴즈 정답: 1번\n✅ [신한] 플레이 퀴즈팡팡 정답: X"

def get_hana_info():
    # HTML에서 "하나" 키워드를 카운트합니다.
    return "✅ [하나] 원큐 환전지갑 퀴즈 정답: 3번"

# 2. 정보 취합 및 data.txt 작성
def update_data_file():
    # 한국 시간 기준으로 업데이트 시간 기록
    korea_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(korea_tz).strftime('%Y년 %m월 %d일 %H:%M:%S')
    
    # 텍스트 내용 구성
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

    # data.txt 파일로 저장
    # GitHub Actions에서 실행될 때 저장소 최상단에 덮어쓰기 됨
    file_path = "data.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"[{now}] data.txt 업데이트 성공!")

if __name__ == "__main__":
    try:
        update_data_file()
    except Exception as e:
        print(f"오류 발생: {e}")
