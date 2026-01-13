import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time

def fetch_lotto_data(round_no):
    """특정 회차(round_no) 데이터를 가져옵니다."""
    url = f"https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo={round_no}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"🔎 {round_no}회차 데이터 확인 중...", end=" ", flush=True)
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # [수정된 부분] 인코딩 설정을 가장 먼저 해야 한글을 인식합니다!
        response.encoding = 'euc-kr' 

        # 이제 한글이 정상적으로 보이므로 검사 가능
        if "당첨결과" not in response.text:
            print("❌ 데이터 없음 (페이지 로딩 실패 또는 없는 회차)")
            return False

        soup = BeautifulSoup(response.text, 'html.parser')

        # 날짜 추출
        date_text = soup.select_one('.win_result .desc')
        if not date_text:
            print("❌ 날짜 파싱 실패")
            return False
            
        date_obj = re.search(r'(\d{4})년 (\d{2})월 (\d{2})일', date_text.text)
        formatted_date = f"{date_obj.group(1)}-{date_obj.group(2)}-{date_obj.group(3)}"

        # 번호 추출
        balls = soup.select('.num.win .ball_645')
        if not balls:
            print("❌ 번호 파싱 실패")
            return False
            
        numbers = [int(ball.text) for ball in balls]
        bonus = int(soup.select_one('.num.bonus .ball_645').text)

        # 등수 정보
        divisions = []
        table_rows = soup.select('.tbl_data.tbl_data_col tbody tr')
        for row in table_rows:
            cols = row.select('td')
            # '데이터가 없습니다' 체크
            if not cols or len(cols) < 4: continue
            
            try:
                prize_text = cols[3].text.strip()
                winners_text = cols[2].text.strip()
                
                # 숫자가 아닌 경우(ex: '0원') 처리
                if '원' not in prize_text and '명' not in winners_text:
                    continue

                prize = int(re.sub(r'[^0-9]', '', prize_text))
                winners = int(re.sub(r'[^0-9]', '', winners_text))
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
            
        print("✅ 다운로드 성공!")
        return True

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return False

def update_force():
    # 1. 내 폴더 확인
    if not os.path.exists('results'):
        os.makedirs('results')
    
    files = [f for f in os.listdir('results') if f.endswith('.json') and f != 'total.json']
    
    if not files:
        # 파일이 없으면 테스트로 1200회부터
        start_round = 1200 
    else:
        # 마지막 저장된 회차 + 1 부터 시작
        saved_rounds = [int(f.replace('.json', '')) for f in files]
        start_round = max(saved_rounds) + 1
    
    print(f"🚀 {start_round}회차부터 업데이트를 시작합니다.")

    # 2. 무한 루프
    current_try = start_round
    while True:
        success = fetch_lotto_data(current_try)
        if not success:
            # 1206회는 성공하고, 1207회에서 실패하며 멈출 것입니다.
            print(f"✋ {current_try}회차는 아직 데이터가 없습니다. 종료합니다.")
            break
        
        current_try += 1
        time.sleep(1) 

    # 3. 합치기
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
    
    print(f"🎉 업데이트 완료! (총 {len(all_data)}개)")

if __name__ == "__main__":
    update_force()
