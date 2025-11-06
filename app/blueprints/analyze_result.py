from flask import Blueprint, jsonify, request
from app import db
from flask_login import current_user, login_required
from datetime import datetime
from ..models.analyze_result import Analyze_result
from ..models.auto import get_class

bp = Blueprint('analyze_result', __name__)
MP = get_class("meds_products")
SP = get_class("supps_products")

@bp.get('/info/<int:product_id>')
def get_drug_info(product_id):
  type_str = request.args.get('type')

  if type_str is None:
    return jsonify({'ok':False, 'message':'type 쿼리스트링 누락'}), 400
  
  try:
    type = int(type_str)
  except ValueError:
    return jsonify({'ok':False, 'message':'type 쿼리스트링 오류'}), 400

  if type == 0:
    model = MP
  elif type == 1:
    model = SP
  else:
    return jsonify({'ok':False, 'message':'type 쿼리스트링 오류 : 0 또는 1이 아닙니다.'}), 400

  # type = 0:의약품, 1:영양제
  info = db.session.query(model).get(product_id)

  if info is None:
    return jsonify({'ok':False, 'message':f'ID {product_id}의 제품 정보를 찾을 수 없습니다.'}), 404

  if type == 0:
    info_data = {
      "id" : info.id, # id
      "product_name" : info.ITEM_NAME, # 품목명
      "manufacturer" : info.ENTP_NAME, # 업체명
      "expiry_info" : info.VALID_TERM, # 유효기간
      "appearance" : info.CHART, # 성상
      "intake_method_doc" : info.UD_DOC_TXT, # 용법용량 문서 데이터
      "effect_doc" : info.EE_DOC_TXT, # 효능효과 문서 데이터
      "caution_doc" : info.NB_DOC_TXT,  # 주의사항(일반) 문서 데이터
      # 의약품 전용 필드
      "main_ingredient" : info.MAIN_ITEM_INGR, # 유효성분
      "additive_name" : info.INGR_NAME,  # 첨가제
      "storage_method" : info.STORAGE_METHOD, # 저장방법
    }
  else:
    info_data = {
      "id" : info.id, # id
      "product_name" : info.PRDLST_NM, # 품목명
      "manufacturer" : info.BSSH_NM, # 업소명
      "expiry_info" : info.POG_DAYCNT, # 소비기한
      "appearance" : info.DISPOS, # 성상
      "intake_method_doc" : info.NTK_MTHD, # 섭취방법
      "effect_doc" : info.PRIMARY_FNCLTY, # 주된기능성
      "caution_doc" : info.IFTKN_ATNT_MATR_CN, # 섭취시주의사항
      # 영양제 전용 필드
      "ingredient" : info.RAWMTRL_NM,  # 원재료
    }

  return jsonify({
    'ok':True,
    'type':type,
    'data':info_data
  }), 200

# @bp.post('/save')
# def save_result():
#   data = request.get_json()
#   result = data.get('result')

#   if result is None:
#     return ({'ok':False, 'message':'분석 결과가 전송되지 않았습니다.'}), 400
  
#   result = Analyze_result(
#     id = id,
#     status = result.status,
#     meds = result.meds,
#     supps = result.supps,
#     duplicates = result.duplicates,
#     interactions = result.interactions
#     user_id = 1 # test
#   )

