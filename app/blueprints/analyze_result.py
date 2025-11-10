from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime
from ..models.analyze_result import Analyze_result
from ..models.auto import get_class
from ..utils.process_ingredients import process_ingredients

from ..extensions import db
from ..models.analyze_result import Analyze_result

bp = Blueprint('analyze_result', __name__)
MP = get_class("meds_products")
SP = get_class("supps_products")

# 분석 후 약 id로 정보 불러오기
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
      "intake_method_doc" : info.UD_DOC_ID, # 용법용량 문서 다운로드 주소
      "effect_doc" : info.EE_DOC_ID, # 효능효과 문서 다운로드 주소
      "caution_doc" : info.NB_DOC_ID,  # 주의사항(일반) 문서 다운로드 주소
      # 의약품 전용 필드
      "main_ingredient" : process_ingredients(info.MAIN_ITEM_INGR), # 유효성분
      "additive_name" : process_ingredients(info.INGR_NAME),  # 첨가제
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
    'info_data':info_data
  }), 200

# 분석 결과 저장
@bp.post('/save')
# @login_required
def save_result():
  result = request.get_json()

  if result is None:
    return jsonify({'ok':False, 'message':'분석 결과가 전송되지 않았습니다.'}), 400
  
  result_data = Analyze_result(
    status = result.get('status'),
    meds = result.get('meds'),
    supps = result.get('supps'),
    duplicates = result.get('duplicates'),
    interactions = result.get('interactions'),
    user_id = 1 # current_user.id
  )

  db.session.add(result_data)

  try:
    db.session.commit()
  except Exception:
    db.session.rollback()
    return jsonify({'ok':False, 'message':'분석 결과 저장 중 오류 발생'}), 400
  
  return jsonify({'ok':True, 'message':'분석 결과 내역에 저장되었습니다.'}), 200

# 분석 결과 목록 불러오기
@bp.get('/history')
# @login_required
def get_history():
  page = request.args.get('page', type=int, default=1)

  # page가 없거나 1보다 작으면 1로 반환
  if page is None and page < 1:
    page = 1

  history = Analyze_result.query.order_by(Analyze_result.analysis_date.desc())

  # history = Analyze_result.query\
  #             .filter(Analyze_result.user_id == current_user.id)\
  #             .order_by(Analyze_result.analysis_date.desc())
  
  try:
    history = history.paginate(page=page, per_page=5, error_out=False)
    
    if page < history.pages and history.total > 0:
      pass
      
  except Exception as e:
    return jsonify({'ok':False, 'message': 'pagination 처리 중 오류 발생'}), 500
  

  pageNumbers = [page for page in history.iter_pages()]

  return jsonify({
    'ok':True,
    'history':[h.to_dict() for h in history.items],
    'total':history.total,
    'has_prev':history.has_prev,
    'has_next':history.has_next,
    'pageNumbers':pageNumbers,
    'pages':history.pages
  })

# 분석 결과 상세 불러오기
@bp.get('/history/detail/<int:id>')
# @login_required
def get_history_detail(id):
  result = db.session.query(Analyze_result).get(id)

  # 로그인한 사용자 아이디와 결과 내역의 유저 아이디와 동일한지 체크
  # if current_user.id != result.user_id:
  #   return jsonify({'ok':False, 'message':'잘못된 접근'}), 403
  
  return jsonify({'ok':True, 'result':result.to_dict()})

# 분석 결과 삭제
@bp.delete('/history/detail/<int:id>')
# @login_required
def delete_history_detail(id):
  result = db.session.query(Analyze_result).get(id)

  # 로그인한 사용자 아이디와 결과 내역의 유저 아이디와 동일한지 체크
  # if current_user.id != result.user_id:
  #   return jsonify({'ok':False, 'message':'잘못된 접근'}), 403

  db.session.delete(result)

  try:
    db.session.commit()
  except Exception:
    db.session.rollback()
    return jsonify({'ok':False, 'message':'분석 결과 삭제 중 오류 발생'}), 500
  
  return ({'ok':True, 'message':'분석 결과가 삭제되었습니다.'})
