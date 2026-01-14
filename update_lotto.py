import requests
import json
import os
from datetime import datetime, timedelta

# 설정
SOURCE_BASE_URL = "https://raw.githubusercontent.com/smok95/lotto/main/winning-stores/"
TARGET_FILE = "results/all_winning_stores.json"

def get_draw_date(drw_no):
    first_draw_date = datetime(2002, 12, 7)
    target_date = first_draw_date + timedelta(days=(int(drw_no) - 1) * 7)
    return target_date.strftime("%Y-%m-%d")

def update():
    # 1. 기존 통합 파일 읽기
    if os.path.exists(TARGET_FILE):
        with open(TARGET_FILE, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    else:
        all_data = []

    # 2. 마지막으로 저장된 회차 확인
    if all_data:
        # 최신순 정렬이므로 첫 번째 항목이 가장 높은 회차
        last_drw = all_data[0]['round']
    else:
        last_drw = 0

    next_drw = last_drw + 1
    new_entries = []

    # 3. 새로운 회차 데이터가 있는지 확인 (최대 5개까지 연속 확인)
    missing_count = 0
    while missing_count < 5:
        url = f"{SOURCE_BASE_URL}{next_drw}.json"
        res = requests.get(url)
        
        if res.status_code == 200:
            stores = res.json()
            missing_count = 0
            if stores:
                clean_stores = [{"name": s.get("name"), "address": s.get("address"), "combination": s.get("combination")} for s in stores]
                new_entries.append({
                    "round": next_drw,
                    "date": get_draw_date(next_drw),
                    "stores": clean_stores
                })
                print(f"회차 {next_drw} 데이터 발견!")
            next_drw += 1
        else:
            missing_count += 1
            next_drw += 1

    # 4. 새로운 데이터가 있다면 맨 앞에 추가하고 저장
    if new_entries:
        # 새 데이터도 최신순으로 정렬 후 기존 데이터 앞에 붙임
        new_entries.sort(key=lambda x: x['round'], reverse=True)
        updated_data = new_entries + all_data
        
        with open(TARGET_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
        print(f"총 {len(new_entries)}개의 회차가 추가되었습니다.")
        return True
    
    print("새로운 데이터가 없습니다.")
    return False

if __name__ == "__main__":
    update()
