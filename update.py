import requests
from bs4 import BeautifulSoup
import json
import re
import os
import sys

def create_lotto_json():
    # ==========================================
    # 1. 최신 회차 크롤링 (동행복권 -> 개별 파일)
    # ==========================================
    # 봇 차단 방지를 위한 헤더 추가 (마치 크롬 브라우저인 척 하기)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    url = "https://dhlottery.co.kr/gameResult.do?method=byWin"
    
    print("🚀 동행복권 사이트에 접속을 시도합니다...", flush=True)
    
    try:
        # headers와 timeout(10초)을 추가해서 접속 요청
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # 404나 500 에러면 즉시 중단
        response.encoding = 'euc-kr'
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # 최신 회차 번호 찾기 (안전하게 가져오기)
        title_tag = soup.select_one('.win_result h4 strong')
        if not title_tag:
            print("❌ 에러: 로또 회차 정보를 찾을 수 없습니다. (사이트 구조 변경 또는 차단 의심)", flush=True)
            print(f"응답 내용 일부: {response.text[:200]}", flush=True) # 디버깅용
            return # 여기서 종료

        title_text = title_tag.text
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
            # 데이터가 '원' '명' 같은 글자가 섞여있으므로 숫자만 추출
            try:
                prize = int(re.sub(r'[^0-9]', '', cols[3].text.strip()))
                winners = int(re.sub(r'[^0-9]', '', cols[2].text.strip()))
                divisions.append({"prize": prize, "winners": winners})
            except (ValueError, IndexError):
                continue

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
            
        print(f"✅ {current_round}회차 크롤링 및 저장 성공!", flush=True)

    except Exception as e:
        print(f"❌ 크롤링 중 치명적인 에러 발생: {e}", flush=True)
        # 깃허브 액션이 실패로 인식하게 하려면 아래 주석을 푸세요
        # sys.exit(1)
        return


    # ==========================================
    # 2. total.json 만들기 (파일 합치기)
    # ==========================================
    print("🔄 total.json 갱신 중...", flush=True)
    
    all_rounds = []
    
    if os.path.exists('results'):
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

    print(f"🎉 total.json 저장 완료! (현재 총 {len(all_rounds)}개 회차 포함됨)", flush=True)

if __name__ == "__main__":
    create_lotto_json()
