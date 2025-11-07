import re

# 의약품 테이블의 MAIN_ITEM_INGR(유효성분), INGR_NAME(첨가제)의
# 기존의 구분자인 |와 [M000000] 코드를 삭제하고
# 배열로 만듦
def process_ingredients(raw_string):
  if not raw_string:
    return []

  # 1. 파이프 기호 (|) 또는 [M000000] 코드를 구분자(예: #TEMP#)로 치환합니다.
  #    이렇게 하면 연속된 구분자나 혼합된 구분자를 모두 처리할 수 있습니다.
  temp_separated = re.sub(r'\||\[M\d{6}\]', '#TEMP#', raw_string)
  
  # 2. 임시 구분자('#TEMP#')를 기준으로 문자열을 분리합니다.
  items = temp_separated.split('#TEMP#')
  
  # 3. 각 항목에서 공백을 제거하고(trim), 빈 문자열을 제거합니다.
  clean_items = [item.strip() for item in items if item.strip()]
  
  return clean_items