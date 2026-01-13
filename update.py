import requests
from bs4 import BeautifulSoup
import json
import re
import os

def create_lotto_json():
    # ==========================================
    # 1. 최신 회차 크롤링 (동행복권 -> 개별 파일)
    # ==========================================
    url = "https://dhlottery.co.kr/gameResult.do?method=byWin"
    response = requests.get(url)
    response.encoding = 'euc-kr'
    soup = BeautifulSoup(response.text, 'html.parser')

    # 최신 회차 번호 찾기
    title_text = soup.select_one('.win_result h4 strong').text
    current_round = int(re.sub(r'[^0-9]', '', title_text))
    
    # 날짜 찾기
    date_text = soup.select_one('.win_result .desc').text
    date_obj = re.search(r'(\d{4})년 (\d{2})월 (\d{2})일', date_text)
    formatted_date = f"{date_obj.group(1)}-{date_obj.group(2)}-{date_obj.group(3)}"

    # 번호 찾기
    balls = soup.select('.num.win .ball_645')
    numbers = [int(ball.text) for ball in balls]
    bonus = int(soup.select_one('.num.bonus .ball_645').text)

    # 등수별 정보
    divisions = []
    table_rows = soup.select('.tbl_data.tbl_data_col tbody tr')
    for row in table_rows:
        cols = row.select('td')
        if not cols: continue
        prize = int(re.sub(r'[^0-9]', '', cols[3].text.strip()))
        winners = int(re.sub(r'[^0-9]', '', cols[2].text.strip()))
        divisions.append({"prize": prize, "winners": winners})

    # 데이터 조립
    winners_combination = {"auto": 0, "manual": 0} 

    result_data = {
        "drwNo": current_round,
        "drwNoDate": formatted_date,
        "drwtNo1": numbers[0],
        "drwtNo2": numbers[1],
        "drwtNo3": numbers[2],
        "drwtNo4": numbers[3],
        "drwtNo5": numbers[4],
        "drwtNo6": numbers[5],
        "bnusNo": bonus,
        "divisions": divisions,
        "winners_combination": winners_combination
    }

    # results 폴더가 없으면 생성
    if not os.path.exists('results'):
        os.makedirs('results')
        
    # 개별 파일 저장 (예: results/1206.json)
    filename = f"results/{current_round}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ {current_round}회차 개별 파일 저장 완료!")


    # ==========================================
    # 2. total.json 만들기 (파일 합치기)
    # ==========================================
    print("🔄 total.json 갱신 중...")
    
    all_rounds = []
    file_list = os.listdir('results')
    
    for fname in file_list:
        # 숫자.json 파일만 골라냅니다 (total.json은 제외)
        if fname.endswith('.json') and fname != 'total.json':
            try:
                with open(os.path.join('results', fname), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_rounds.append(data)
            except:
                continue
    
    # 회차순으로 정렬 (최신 회차가 위로 오게 reverse=True)
    all_rounds.sort(key=lambda x: x['drwNo'], reverse=True) 
    
    # total.json 저장
    with open('results/total.json', 'w', encoding='utf-8') as f:
        json.dump(all_rounds, f, indent=2, ensure_ascii=False)

    print(f"🎉 total.json 저장 완료! (현재 총 {len(all_rounds)}개 회차 포함됨)")

if __name__ == "__main__":
    create_lotto_json()
