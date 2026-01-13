import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time

def fetch_lotto_data(round_no):
    url = f"https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo={round_no}"
    # 헤더를 더 진짜 브라우저처럼 보강
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://dhlottery.co.kr/",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    print(f"🔎 {round_no}회차 시도 중...", end=" ", flush=True)
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # EUC-KR로 강제 디코딩 (가장 안전한 방법)
        html_text = response.content.decode('euc-kr', 'replace')

        # 1. 봇 차단이나 엉뚱한 페이지인지 확인
        soup = BeautifulSoup(html_text, 'html.parser')
        page_title = soup.title.text if soup.title else "제목없음"
        
        if "동행복권" not in page_title and "당첨결과" not in html_text:
            print(f"\n❌ 실패: 사이트가 엉뚱한 페이지를 줬습니다. (제목: {page_title})")
            print("   -> 깃허브 서버 IP가 차단되었을 가능성이 높습니다.")
            return False

        if "당첨결과" not in html_text:
            print("\n❌ 실패: 페이지는 열렸으나 '당첨결과' 텍스트가 없습니다.")
            return False

        # 2. 날짜 파싱
        date_text = soup.select_one('.win_result .desc')
        if not date_text:
            print("\n❌ 실패: 날짜 정보를 못 찾았습니다.")
            return False
            
        date_obj = re.search(r'(\d{4})년 (\d{2})월 (\d{2})일', date_text.text)
        formatted_date = f"{date_obj.group(1)}-{date_obj.group(2)}-{date_obj.group(3)}"

        # 3. 번호 파싱
        balls = soup.select('.num.win .ball_645')
        if not balls:
            print("\n❌ 실패: 번호 공(ball)을 못 찾았습니다.")
            return False
            
        numbers = [int(ball.text) for ball in balls]
        bonus = int(soup.select_one('.num.bonus .ball_645').text)

        # 4. 등수 정보
        divisions = []
        table_rows = soup.select('.tbl_data.tbl_data_col tbody tr')
        for row in table_rows:
            cols = row.select('td')
            if not cols or len(cols) < 4: continue
            try:
                prize = int(re.sub(r'[^0-9]', '', cols[3].text.strip()))
                winners = int(re.sub(r'[^0-9]', '', cols[2].text.strip()))
                divisions.append({"prize": prize, "winners": winners})
            except:
                continue

        result_data = {
            "drwNo": round_no,
            "drwNoDate": formatted_date,
            "drwtNo1": numbers[0], "drwtNo2": numbers[1], "drwtNo3": numbers[2],
            "drwtNo4": numbers[3], "drwtNo5": numbers[4], "drwtNo6": numbers[5],
            "bnusNo": bonus,
            "divisions": divisions,
            "winners_combination": {"auto": 0, "manual": 0}
        }

        # 파일 저장
        if not os.path.exists('results'):
            os.makedirs('results')
        
        with open(f"results/{round_no}.json", 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
            
        print("✅ 성공! 파일 생성됨.")
        return True

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        return False

def update_force():
    if not os.path.exists('results'):
        os.makedirs('results')
    
    # 저장된 파일 확인
    files = [f for f in os.listdir('results') if f.endswith('.json') and f != 'total.json']
    if not files:
        start_round = 1205 # 테스트용 시작점
    else:
        saved_rounds = [int(f.replace('.json', '')) for f in files]
        start_round = max(saved_rounds) + 1
    
    print(f"🚀 {start_round}회차부터 업데이트 시작!")

    # 연속 3번 실패하면 멈춤 (무한루프 방지)
    fail_count = 0
    current_try = start_round
    
    while True:
        success = fetch_lotto_data(current_try)
        if success:
            fail_count = 0
            current_try += 1
            time.sleep(2) # 차단 방지를 위해 2초 대기
        else:
            fail_count += 1
            print(f"   (실패 {fail_count}/3)")
            if fail_count >= 3:
                print("✋ 3회 연속 실패로 종료합니다.")
                break
            current_try += 1
            time.sleep(2)

    # 합치기
    print("🔄 total.json 갱신 중...", flush=True)
    all_data = []
    files = os.listdir('results')
    for fname in files:
        if fname.endswith('.json') and fname != 'total.json':
            try:
                with open(os.path.join('results', fname), 'r', encoding='utf-8') as f:
                    all_data.append(json.load(f))
            except: pass
    
    all_data.sort(key=lambda x: x['drwNo'], reverse=True)
    with open('results/total.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    update_force()
