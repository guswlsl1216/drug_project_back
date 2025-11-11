from flask import Blueprint, jsonify, request
from app import db
from flask_login import current_user, login_required
from ..models.auto import get_class
from sqlalchemy import or_, func
import uuid
import random

bp = Blueprint('aiAnalyze', __name__)
 
# 모델 클래스 정의
MP = get_class("meds_products")
SP = get_class("supps_products")

# --- 모의(Mock) 부작용 및 중복 성분 검색 함수 (실제 DB 로직 대체) ---

# 실제로는 DB에서 성분1과 성분2의 상호작용 데이터를 조회해야 합니다.
def mock_get_interaction_data(product1, ingredient1, product2, ingredient2):
    """
    두 성분 간의 상호작용 데이터를 모의로 반환
    DB 상호작용 테이블을 쿼리해야한다 ------
    """
    
    # 예시 상호작용 규칙 (실제 DB 규칙으로 대체 필요)
    # 이부프로펜 + 오메가-3 상호작용 예시
    if "이부프로펜" in ingredient1 and "오메가-3" in ingredient2:
        return {
            "level": 1,
            "message": "출혈의 위험을 증가시킬 수 있어요!"
        }
    # 클래리트로마이신 + 심바스타틴 상호작용 예시
    if "클래리트로마이신" in ingredient1 and "심바스타틴" in ingredient2:
        return {
            "level": 2,
            "message": "근병증, 횡문근융해의 위험증가"
        }
        
    # 두 성분이 '비타민'을 포함하고 레벨 0을 반환하는 예시
    if "비타민" in ingredient1 and "비타민" in ingredient2:
        return {
            "level": 0,
            "message": "일반적인 비타민 보충입니다."
        }
        
    # 상호작용이 없는 경우
    return None

def extract_supp_ingredients(ingredients_str):
    """
    영양제 성분 문자열을 분석하여 주요 성분 리스트를 반환합니다.
    쉼표(,)를 기준으로 나누되, 괄호 안의 내용은 무시하지 않고 포함합니다.
    """
    # 쉼표를 기준으로 나눈 후 공백을 제거하고, 빈 문자열을 제거합니다.
    ingredients = [s.strip() for s in ingredients_str.split(',') if s.strip()]
    return ingredients


# --- API 엔드포인트: 제품 검색 ---

@bp.route('/medicine/search', methods=['GET'])
@bp.route('/supplements/search', methods=['GET'])
def search_meds():
    search_name = request.args.get('q', '').strip()
    search_type = request.args.get('type')

    if not search_type or search_type not in ['supps', 'meds']:
        return jsonify({ 'error' : 'type은 반드시 meds 또는 supps 여야 합니다. '}), 400
    
    model = SP if search_type == 'supps' else MP

    if search_type == 'supps':
        column_name = model.PRDLST_NM
        ingredient_column = model.RAWMTRL_NM
    else:
        column_name = model.ITEM_NAME
        ingredient_column = model.MAIN_INGR_ENG

    # 검색어가 너무 짧거나 없으면 결과를 반환하지 않습니다. (디바운스된 프론트와 연동)
    if not search_name:
        return jsonify({
            'success': True,
            'medicines': [] 
        })

    normalized_search_name = search_name.replace(' ', '').lower()
    search_keyword = f"%{normalized_search_name}%"

    # 상위 50개만 검색 (성능 최적화)
    results = (
        db.session.query(model.id, column_name, ingredient_column) 
        .filter(
          func.lower(func.replace(column_name, ' ', '')).like(search_keyword)
        ).limit(50).all()
    )

    data = []
    for r in results:
          item_id, item_name, item_ingredients = r
          
          # DB 성분 값이 None일 경우 빈 문자열로 처리
          processed_ingredients = item_ingredients if item_ingredients is not None else ""
          
          data.append({ 
              "id" : item_id, 
              "name" : item_name,
              # 'ingredients'는 성분 값입니다.
              "ingredients": processed_ingredients 
          })


    return jsonify({
        'success': True,
        # 프론트엔드에서 'medicines' 키를 사용하므로 이 키로 데이터를 담습니다.
        'medicines': data 
      })

# --- API 엔드포인트: 분석 결과 요청 ---

@bp.post('/analyze/result')
def analyze_result():
    data = request.get_json()
    meds = data.get('meds', [])
    supps = data.get('supps', [])
    
    # 1. 초기화
    interactions = []
    duplicates = {}  # {성분명: [제품명1, 제품명2, ...]}
    max_level = 0
    
    # 2. 영양제 성분 리스트 추출 및 중복 확인을 위한 준비
    all_supp_ingredients = []
    
    for supp in supps:
        # 영양제는 성분을 쉼표로 분리하여 각 성분별로 중복 및 상호작용 검사 준비
        supp_ingredients = extract_supp_ingredients(supp.get('ingredients', ''))
        supp['processed_ingredients'] = supp_ingredients # 처리된 성분 리스트 저장
        all_supp_ingredients.extend(supp_ingredients)
        
        # 영양제 성분 중복 검사 (제품명 리스트 저장)
        for ingr in supp_ingredients:
            if ingr not in duplicates:
                duplicates[ingr] = []
            duplicates[ingr].append(supp['name'])


    # 3. 의약품 성분 중복 검사
    for med in meds:
        # 의약품 성분은 하나로 가정하고 처리
        ingr = med.get('ingredients', '')
        if ingr:
            if ingr not in duplicates:
                duplicates[ingr] = []
            duplicates[ingr].append(med['name'])


    # 4. 상호작용 검사: 의약품 vs 영양제 (Level 1)
    if supps: # 영양제가 0개면 할 필요 없음
        for med in meds:
            for supp in supps:
                # 영양제의 모든 성분과 의약품 성분 비교
                for supp_ingr in supp.get('processed_ingredients', []):
                    interaction = mock_get_interaction_data(
                        med['name'], med['ingredients'],
                        supp['name'], supp_ingr
                    )
                    
                    if interaction:
                        interactions.append({
                            "product1_name": med['name'],
                            "ingredient1": med['ingredients'],
                            "product2_name": supp['name'],
                            "ingredient2": supp_ingr,
                            "level": 1,
                            "message": interaction['message']
                        })
                        max_level = max(max_level, 1) # max_level 업데이트

    
    # 5. 상호작용 검사: 의약품 vs 의약품 (Level 2)
    if len(meds) >= 2: # 의약품이 2개 이상일 때만 비교
        for i in range(len(meds)):
            for j in range(i + 1, len(meds)):
                med1 = meds[i]
                med2 = meds[j]
                
                # 의약품 성분끼리 비교
                interaction = mock_get_interaction_data(
                    med1['name'], med1['ingredients'],
                    med2['name'], med2['ingredients']
                )
                
                if interaction:
                    interactions.append({
                        "product1_name": med1['name'],
                        "ingredient1": med1['ingredients'],
                        "product2_name": med2['name'],
                        "ingredient2": med2['ingredients'],
                        "level": 2,
                        "message": interaction['message']
                    })
                    max_level = max(max_level, 2) # max_level 업데이트


    # 6. 최종 중복 데이터 형식 정리
    final_duplicates = []
    # 중복된 제품이 2개 이상일 때만 추가
    for ingredient, names in duplicates.items():
        if len(names) > 1:
            final_duplicates.append({
                "ingredient": ingredient,
                "names": names
            })

    # 7. 응답 객체 생성 및 반환
    # status는 상호작용 level의 최대값으로 설정
    # 만약 상호작용이 없다면 (max_level=0) status를 0으로 설정
    response_data = {
        "analysis_uid": str(uuid.uuid4()),
        "status": max_level if max_level > 0 else 0, # 부작용 레벨을 status로 사용
        "meds": meds,
        "supps": supps,
        "duplicates": final_duplicates,
        "interactions": interactions,
    }
    
    return jsonify(response_data)