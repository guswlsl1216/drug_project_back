from flask import Blueprint, jsonify, request
from app import db
from flask_login import current_user, login_required
from ..models.auto import get_class
from sqlalchemy import or_
from sqlalchemy import func

bp = Blueprint('aiAnalyze', __name__)
  
MP = get_class("meds_products")
SP = get_class("supps_products")

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
    #  영양제 모델(SP)의 성분 컬럼을 NUTRITIONAL_FUNCTIONAL_MATERIAL로 가정하고 설정
    #  만약 이 컬럼명이 다를 경우, 실제 영양제 테이블의 성분 컬럼명으로 변경해야 합니다.
    ingredient_column = model.RAWMTRL_NM
  else:
    column_name = model.ITEM_NAME
    # 의약품 성분 컬럼: MAIN_INGR_ENG 사용 확정
    ingredient_column = model.MAIN_INGR_ENG


  normalized_search_name = search_name.replace(' ', '').lower()
  search_keyword = f"%{normalized_search_name}%"

  results = (
    db.session.query(model.id, column_name, ingredient_column) 
    .filter(
      func.lower(func.replace(column_name, ' ', '')).like(search_keyword)
    ).all()
  )

  data = []
  for r in results:
      item_id, item_name, item_ingredients = r
      
      # DB 성분 값이 None일 경우, 프론트엔드의 'undefined' 에러를 막기 위해 빈 문자열로 처리
      processed_ingredients = item_ingredients if item_ingredients is not None else ""
      
      data.append({ 
          "id" : item_id, 
          "name" : item_name,
          "ingredients": processed_ingredients # 성분 값 포함
      })


  return jsonify({
        'success': True,
        # 프론트엔드가 'medicines' 키를 예상하므로 여기에 데이터를 담습니다.
        'medicines': data 
    })

