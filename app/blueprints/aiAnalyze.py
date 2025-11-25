from flask import Blueprint, jsonify, request, current_app
from app import db
from flask_login import current_user, login_required
from ..models.auto import get_class
from sqlalchemy import or_, func
import uuid
import random
import os
from ..utils.process_ingredients import process_ingredients

bp = Blueprint('aiAnalyze', __name__)


# 모델 클래스 정의
MP = get_class("meds_products")
SP = get_class("supps_products")
# ⭐ 의약품-의약품 상호작용 테이블 (drug_contraindication)
Interaction = get_class("drug_contraindications") 
# ⭐ 영양제-의약품 상호작용 테이블 (supps_meds_interaction)
SuppsMedsInteraction = get_class("supps_meds_interaction")


# --- 유틸리티 함수 ---

def safe_ingredient_str(ingr_data):
    """
    의약품 성분 데이터를 안전하게 문자열로 변환합니다.
    데이터가 리스트인 경우 공백으로 연결하고, 아니면 문자열로 변환 후 공백을 제거합니다.
    """
    if isinstance(ingr_data, list):
        # 리스트의 모든 요소를 공백으로 연결
        return ' '.join([str(item).strip() for item in ingr_data]).strip()
    
    # None이거나 기타 타입인 경우 문자열로 변환 후 공백 제거
    return str(ingr_data).strip()

def extract_supp_ingredients(ingredients_str):
    """
    영양제 성분 문자열을 분석하여 주요 성분 리스트를 반환합니다.
    쉼표(,)를 기준으로 나누되, 빈 문자열은 제거합니다.
    """
    if not isinstance(ingredients_str, str):
        # 문자열이 아니면 빈 리스트 반환 (프론트엔드에서 숫자형 ID가 넘어오는 경우 대비)
        return []

    # 쉼표를 기준으로 나눈 후 공백을 제거하고, 빈 문자열을 제거합니다.
    # 괄호 안의 내용이나 불필요한 부분을 제거하기 위해 split('(')[0]을 적용
    ingredients = [s.strip().split('(')[0] for s in ingredients_str.split(',') if s.strip()]
    return ingredients

# --- 실제 DB 부작용 및 중복 성분 검색 함수 (현재 analyze_result에서는 사용되지 않지만 코드 안전성 확보) ---

def get_actual_interaction_data(product1, ingredient1, product2, ingredient2):
    """
    두 성분(ingredient1, ingredient2) 간의 의약품-의약품 상호작용 데이터를 DB에서 조회합니다.
    (drug_contraindication 테이블 쿼리)
    """
    
    # 성분명에서 괄호 안의 내용이나 불필요한 부분을 제거하고 표준화합니다.
    ingr1_clean = ingredient1.strip().split('(')[0].lower()
    ingr2_clean = ingredient2.strip().split('(')[0].lower()
    
    # 1. DB 쿼리 실행 (의약품-의약품)
    # 성분 1과 성분 2가 DRUG_CONTRA_NAME/DRUG_CONTRA_INGR 필드에 어떻게 조합되어 있는지 검색합니다.
    query = (
        db.session.query(
            Interaction.TYPE_CODE, 
            Interaction.SEEK_TO_REASON 
        )
        .filter(
            or_(
                # 케이스 1: (성분1 vs 성분2)
                (func.lower(Interaction.DRUG_CONTRA_NAME) == ingr1_clean) & 
                (func.lower(Interaction.DRUG_CONTRA_INGR) == ingr2_clean),
                # 케이스 2: (성분2 vs 성분1) (순서 변경)
                (func.lower(Interaction.DRUG_CONTRA_NAME) == ingr2_clean) & 
                (func.lower(Interaction.DRUG_CONTRA_INGR) == ingr1_clean)
            )
        )
    )

    result = query.first()

    if result:
        level_code, warning_message = result
        
        # TYPE_CODE를 기반으로 위험 레벨 결정 (의약품-의약품 상호작용은 Level 2로 가정)
        # 🚨 실제 TYPE_CODE의 의미에 따라 이 매핑 로직은 변경되어야 합니다.
        if level_code and str(level_code).startswith('200'):
             level = 2
        elif level_code and str(level_code).startswith('100'):
             level = 1
        else:
             level = 0
        
        return {
            "level": level,
            "message": warning_message # SEEK_TO_REASON 컬럼의 내용을 그대로 사용
        }
        
    # 상호작용이 없는 경우
    return None


def get_supps_meds_interaction_data(supp_ingredient, med_ingredient, product_name_med):
    """
    영양제 성분(supp_ingredient)과 의약품 성분(med_ingredient) 간의 상호작용을 DB에서 조회합니다.
    (supps_meds_interaction 테이블 쿼리)
    """
    # 영양제 성분과 의약품 성분명을 모두 소문자로 표준화합니다.
    supp_ingr_clean = supp_ingredient.strip().split('(')[0].lower()
    med_ingr_clean = med_ingredient.strip().split('(')[0].lower()
    
    # 1. DB 쿼리 실행
    # 영양제 성분(ingredient)과 의약품 성분(caution_drug)을 모두 포함하는 레코드를 검색합니다.
    query = (
        db.session.query(
            SuppsMedsInteraction.warning_text
        )
        .filter(
            # 영양제 성분이 DB의 ingredient 컬럼에 포함되는지 확인 (LIKE 사용)
            # 의약품 성분이 DB의 caution_drug 컬럼에 포함되는지 확인 (LIKE 사용)
            # 🚨 주의: 정확한 매칭이 필요할 수 있으나, 여기서는 일단 LIKE를 사용합니다.
            func.lower(SuppsMedsInteraction.ingredient).like(f"%{supp_ingr_clean}%"),
        func.lower(SuppsMedsInteraction.caution_drug).like(f"%{med_ingr_clean}%")
        )
    )

    result = query.first()

    if result:
        warning_message = result[0] # warning_text 컬럼
        
        # 영양제-의약품 상호작용은 '주의' 레벨 (Level 1)로 고정합니다.
        return {
            "level": 1,
            "message": warning_message 
        }
        
    # 상호작용이 없는 경우
    return None


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
        kor_name_column = model.RAWMTRL_NM
    else:
        column_name = model.ITEM_NAME
        ingredient_column = model.MAIN_INGR_ENG
        kor_name_column = model.MAIN_ITEM_INGR

    if not search_name:
        return jsonify({
            'success': True,
            'medicines': [] 
        })

    normalized_search_name = search_name.replace(' ', '').lower()
    search_keyword = f"%{normalized_search_name}%"

    results = (
        db.session.query(model.id, column_name, ingredient_column, kor_name_column) 
        .filter(
          func.lower(func.replace(column_name, ' ', '')).like(search_keyword)
        ).limit(50).all()
    )

    data = []
    for r in results:
          item_id, item_name, item_ingredients, item_korname = r
          
          # ingredient_column의 값이 None일 경우 처리
          processed_ingredients = item_ingredients if item_ingredients is not None else ""

          # korName이 비어있거나 None일 경우, item_name(제품명)을 대체값으로 사용
          final_kor_name = item_korname
          if search_type == 'supps' and (final_kor_name is None or str(final_kor_name).strip() == ""):
              final_kor_name = item_name
          # 의약품의 경우도 혹시 모를 None 방지
          elif final_kor_name is None:
              final_kor_name = ""

          data.append({
              "id" : item_id,
              "name" : item_name,
              "ingredients": processed_ingredients,
              # 프론트엔드와 통일: 'kor-name' -> 'korName' (camelCase)
              "korName": process_ingredients(final_kor_name), 
          })

    return jsonify({
        'success': True,
        'medicines': data 
      })

# --- API 엔드포인트: 분석 결과 요청 ---

@bp.route('/analyze/result', methods=['POST'])
def analyze_result():
    
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            "analysis_uid": str(uuid.uuid4()),
            "status": -1,
            "message": "요청 데이터가 비어있습니다.",
            "meds": [],
            "supps": []
        }), 400

    meds = data.get('meds', [])
    supps = data.get('supps', [])
    interactions = []
    duplicates = []
    max_level = 0 # 전체 위험도 상태 추적

    print(data)

    # ==========================
    # 1️⃣ 영양제 - 의약품 상호작용 검색 (level 1)
    # ==========================
    for med in meds:
        # 안전한 성분 문자열 추출 (리스트 입력 방지)
        med_ingr = safe_ingredient_str(med.get('ingredients', ''))
        
        if not med_ingr: # 의약품 성분이 없는 경우 건너뛰기
            continue

        med_ingr_clean = med_ingr.lower()
        
        for supp in supps:
            # 영양제 성분 추출 (extract_supp_ingredients 함수가 이미 안전하게 처리)
            supp_ingredients = extract_supp_ingredients(supp.get('ingredients', ''))
            
            for supp_ingr in supp_ingredients:
                supp_ingr_clean = supp_ingr.split('(')[0].strip().lower()
                
                # ==============================================================
                # 1단계: 일반 경고 (Caution Drug 필드가 비어있는 경우) 검색
                # ==============================================================
                
                general_warning_query = db.session.query(
                    SuppsMedsInteraction.warning_text
                ).filter(
                    # 영양제 성분 매칭
                    func.lower(supp_ingr_clean).like(func.lower(func.concat('%', SuppsMedsInteraction.ingredient, '%'))),
                    
                    # caution_drug 필드가 비어있는 레코드를 찾음 (NULL 또는 빈 문자열)
                    (SuppsMedsInteraction.caution_drug == None) | (SuppsMedsInteraction.caution_drug == '')
                ).first()

                if general_warning_query:
                    # 일반 경고는 항상 interactions 리스트에 추가
                    warning_message = general_warning_query[0]
                    interactions.append({
                        "product1_name": supp['name'],
                        "ingredient1": supp_ingr,
                        "product2_name": med['name'],
                        "ingredient2": safe_ingredient_str(med.get('korName', '')), 
                        "level": 1,
                        "message": warning_message
                    })
                    max_level = max(max_level, 1)

                # ==============================================================
                # 2단계: 특정 의약품 상호작용 검색 (Caution Drug 필드에 값이 있는 경우)
                # ==============================================================
                
                specific_interaction_query = db.session.query(
                    SuppsMedsInteraction.warning_text
                ).filter(
                    # 영양제 성분 매칭
                    func.lower(supp_ingr_clean).like(func.lower(func.concat('%', SuppsMedsInteraction.ingredient, '%'))),
                    
                    # 특정 의약품 성분 매칭
                    func.lower(SuppsMedsInteraction.eng_caution_drug).like(f"%{med_ingr_clean}%")
                ).first()

                if specific_interaction_query:
                    warning_message = specific_interaction_query[0]
                    interactions.append({
                        "product1_name": supp['name'],
                        "ingredient1": supp_ingr,
                        "product2_name": med['name'],
                        "ingredient2": safe_ingredient_str(med.get('korName', '')), # 한국어 성분명 사용
                        "level": 1,
                        "message": warning_message
                    })
                    max_level = max(max_level, 1)

    # ==========================
    # 2️⃣ 의약품 - 의약품 상호작용 검색 (level 2)
    # ==========================
    if len(meds) > 1:
        for i in range(len(meds)):
            for j in range(i + 1, len(meds)):
                med1 = meds[i]
                med2 = meds[j]
                
                # 안전한 성분 문자열 추출
                ingr1 = safe_ingredient_str(med1.get('ingredients', ''))
                ingr2 = safe_ingredient_str(med2.get('ingredients', ''))
                
                if not ingr1 or not ingr2:
                    continue

                # 금기성분 테이블 조회를 위한 성분 표준화
                ingr1_clean = ingr1.strip().split('(')[0].lower()
                ingr2_clean = ingr2.strip().split('(')[0].lower()
                
                # 금기성분 테이블 조회 (DB 쿼리)
                query = db.session.query(Interaction.금기사유).filter(
                    or_(
                        (Interaction.성분명1 == ingr1_clean) & (Interaction.성분명2 == ingr2_clean),
                        (Interaction.성분명1 == ingr2_clean) & (Interaction.성분명2 == ingr1_clean)
                    )
                ).distinct().all()

                # korName 추출 (med1에서만 추출하는 것이 아니라, 각 제품에서 추출해야 함)
                kor_ingr1 = safe_ingredient_str(med1.get('korName', ''))
                kor_ingr2 = safe_ingredient_str(med2.get('korName', ''))
                
                if query:
                    for row in query:
                        warning_message = row[0]
                        interactions.append({
                            "product1_name": med1['name'],
                            "ingredient1": kor_ingr1, # 한국어 성분명 사용 (process_ingredients는 불필요)
                            "product2_name": med2['name'],
                            "ingredient2": kor_ingr2, # 한국어 성분명 사용
                            "level": 2,
                            "message": warning_message
                        })
                        max_level = max(max_level, 2)

    # ==========================
    # 3️⃣ 중복 성분 검사 (영양제 + 의약품)
    # ==========================
    ingredient_map = {}

    # 의약품
    for med in meds:
        # 🚨 여기서 오류가 발생할 수 있었으므로, safe_ingredient_str 적용
        ingr = safe_ingredient_str(med.get('ingredients', ''))
        
        if not ingr:
            continue
        ingredient_map.setdefault(ingr, []).append(med['name'])

    # 영양제
    for supp in supps:
        supp_ingredients = extract_supp_ingredients(supp.get('ingredients', ''))
        for ingr in supp_ingredients:
            # extract_supp_ingredients에서 이미 괄호 안의 내용이 제거됨
            ingr_clean = ingr.strip() 
            ingredient_map.setdefault(ingr_clean, []).append(supp['name'])

    for ingr, names in ingredient_map.items():
        if len(names) > 1:
            duplicates.append({
                "ingredient": ingr,
                "names": names
            })

    # ==========================
    # 4️⃣ 최종 결과 응답
    # ==========================
    response = {
        "analysis_uid": str(uuid.uuid4()),
        "status": max_level if max_level > 0 else 0,
        "meds": meds,
        "supps": supps,
        "duplicates": duplicates,
        "interactions": interactions
    }

    print("AI 분석 결과:==================================")
    print(response)

    return jsonify(response)


# 분석 요청한 의약품 이미지 임시 저장
@bp.post("/images/temp")
def image_temp():
    img_file = request.files.get('file') or None

    if img_file:
        unique_filename = str(uuid.uuid4())
        file_extension = img_file.filename.rsplit('.', 1)[1].lower() if '.' in img_file.filename else 'png'
        final_filename = f"{unique_filename}.{file_extension}"

        save_subdir = current_app.config.get("UPLOAD_TEMP", "temp")
        save_dir = os.path.join(current_app.root_path, 'static', save_subdir)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    save_path = os.path.join(save_dir, final_filename)

    try:
        img_file.save(save_path)
        public_url = f'/static/temp/{final_filename}'
        return jsonify({'ok': True, 'message': '이미지가 임시 저장되었습니다.', 'image_url': public_url}), 200
    except Exception as e:
        print(f"이미지 저장 중 오류 발생: {e}")
        return jsonify({'ok': False, 'message': '이미지 저장 중 오류가 발생했습니다.'}), 500
    