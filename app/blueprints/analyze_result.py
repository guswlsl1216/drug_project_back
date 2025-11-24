from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from flask_jwt_extended import get_current_user, jwt_required
from datetime import datetime
from ..models.analyze_result import Analyze_result
from ..models.auto import get_class
from ..utils.process_ingredients import process_ingredients
from ..utils.requires_ownership import requires_ownership

from ..extensions import db
from ..models.analyze_result import Analyze_result

from ultralytics import YOLO
import io
from PIL import Image
import os, json, uuid

# analyze_result.py가 위치한 폴더의 경로 (drug_project_back/app/blueprints)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# blueprint -> app -> drug_project_back
PROJECT_ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))

# 최종 모델 경로를 절대 경로로 조합
MODEL_PATH = os.path.join(
  PROJECT_ROOT_DIR,
  'runs',
  'detect',
  'train',
  'weights',
  'best.pt'
)

print(f"모델 예상 절대 경로: {MODEL_PATH}")

try:
  yolo_model = YOLO(MODEL_PATH)
  print("YOLO 모델 서버에 성공적으로 로드")
except Exception as e:
  print(f"모델 로드 오류: {e}")
  yolo_model = None # 로드 실패 시 None으로 설정

bp = Blueprint('analyze_result', __name__)
MP = get_class("meds_products")
SP = get_class("supps_products")


@bp.post('/detect')
def detect_drug_label():

  # 모델 로드 상태 확인
  if yolo_model is None:
    return jsonify({"ok":False, "message": "모델이 메모리에 로드되지 않았습니다."}), 503
  
  # 파일 첨부 여부 확인
  if 'file' not in request.files:
    return jsonify({'ok': False, "message": "이미지 파일이 필요합니다. (file 키 누락)"}), 400

  file = request.files['file']

  try:
    image_bytes = file.read()
    image = Image.open(io.BytesIO(image_bytes))

    # conf: 0.25 이상의 신뢰도만 반환
    results = yolo_model(image, imgsz=640, conf=0.25)

    detections = []
    for r in results:
      boxes = r.boxes.xyxy.cpu().tolist()
      confs = r.boxes.conf.cpu().tolist()
      cls = r.boxes.cls.cpu().tolist()

      for box, conf, cl in zip(boxes, confs, cls):

        drug_id = yolo_model.names[int(cl)]
        print(f"✅ 탐지된 약물: ID={drug_id}, 신뢰도={round(conf, 4)}")
        
        # 추가된 로직: ITEM_SEQ로 DB에서 ITEM_NAME 조회
        product_info = db.session.query(MP.ITEM_NAME).filter(
					MP.ITEM_SEQ == drug_id
				).first()
    
        # 실제 제품명 (조회 실패 시 ITEM_SEQ를 대체값으로 사용)
        product_name = product_info[0] if product_info else f"제품명 조회 실패 (ITEM_SEQ: {drug_id})"

        detections.append({
          "box": [round(x) for x in box],
          "confidence": round(conf, 4),
          "class_id": int(cl),
          "class_name": drug_id,
          "product_name": product_name
        })

    return jsonify({"ok":True, "message":"이미지 탐지 완료", "detections":detections}), 200
  
  except Exception as e:
    print(f"YOLOv8 추로 API 오류 발생: {e}")
    return jsonify({"ok":False, "message":f"추론 중 서버 내부 오류 발생: {str(e)}"}), 500


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
@jwt_required()
def save_result():
  user = get_current_user()
  user_id = user.id

  img_file = request.files.get('file') or None
  result_json_string = request.form.get('result')
  if result_json_string is None:
    return jsonify({'ok':False, 'message':'분석 결과가 전송되지 않았습니다.'}), 400
  
  try:
    result = json.loads(result_json_string) 
  except json.JSONDecodeError:
    return {"error": "result_data JSON 파싱 오류."}, 400
  
  # 중복 저장 방지
  if Analyze_result.query.filter_by(
    user_id=user_id,
    analysis_uid=result['analysis_uid']
  ).first():
    return jsonify({'ok': False, 'message': '이미 저장된 분석 결과입니다.'}), 400
  
  if img_file:
    unique_filename = str(uuid.uuid4())
    file_extension = img_file.filename.rsplit('.', 1)[1].lower() if '.' in img_file.filename else 'png'
    final_filename = f"{unique_filename}.{file_extension}"

    save_dir = os.path.join(current_app.root_path, 'static', 'analyze')

    if not os.path.exists(save_dir):
      os.makedirs(save_dir)

    save_path = os.path.join(save_dir, final_filename)

    try:
      img_file.save(save_path)
      public_url = f'/static/analyze/{final_filename}'
      result['image_url'] = public_url
    except Exception as e:
      print(f"이미지 저장 중 오류 발생: {e}")
      return jsonify({'ok': False, 'message': '이미지 저장 중 오류가 발생했습니다.'}), 500
  
  result_model = Analyze_result(**result, user_id=user_id)

  db.session.add(result_model)

  try:
    db.session.commit()
  except Exception:
    db.session.rollback()
    os.remove(save_path)
    return jsonify({'ok':False, 'message':'분석 결과 저장 중 오류 발생'}), 400
  
  return jsonify({
    'ok':True,
    'message':'분석 결과 내역에 저장되었습니다.',
    'isSave':True
  }), 200

# 분석 결과 목록 불러오기
@bp.get('/history')
@jwt_required()
def get_history():
  user = get_current_user()
  current_user_id = user.id
  page = request.args.get('page', type=int, default=1)
  per_page = request.args.get("per_page", 10, type=int)

  # page가 1보다 작으면 1로 반환
  if page < 1:
    page = 1

  history = Analyze_result.query\
              .filter(Analyze_result.user_id == current_user_id)\
              .order_by(Analyze_result.analysis_date.desc())
  
  try:
    history = history.paginate(page=page, per_page=per_page, error_out=False)
    
    # 요청된 페이지가 전체 페이지 수를 초과하는 경우 마지막 페이지로
    if page > history.pages and history.total > 0:
      page = history.pages
      history = history.paginate(page=page, per_page=per_page, error_out=False)
        
    # 항목이 아예 없는 경우 빈 페이지 반환
    elif history.total == 0:
      pass
      
  except Exception as e:
    return jsonify({'ok':False, 'message': 'pagination 처리 중 오류 발생'}), 500

  return jsonify({
    'ok':True,
    'history':[h.to_dict() for h in history.items],
    'total':history.total,
    'page':history.page,
    'pages':history.pages,
    'per_page':history.per_page
  }), 200

# 분석 결과 상세 불러오기
@bp.get('/history/detail/<int:id>')
@jwt_required()
@requires_ownership(model=Analyze_result, url_id_field='id', user_field='user_id')
def get_history_detail(id):
  result = db.session.query(Analyze_result).get(id)

  return jsonify({'ok':True, 'result':result.to_dict()})

# 분석 결과 삭제
@bp.delete('/history/detail/<int:id>')
@jwt_required()
@requires_ownership(Analyze_result)
def delete_history_detail(id):
  result = db.session.query(Analyze_result).get(id)
  image_url = result.image_url

  db.session.delete(result)

  try:
    db.session.commit()

    if image_url:
      file_path = os.path.join(current_app.root_path, image_url.lstrip('/'))
      
      if os.path.exists(file_path):
        try:
          os.remove(file_path)
        except Exception as e:
          print(f"이미지 파일 삭제 실패 ({file_path}): {e}")
  except Exception:
    db.session.rollback()
    return jsonify({'ok':False, 'message':'분석 결과 삭제 중 오류 발생'}), 500
  
  return ({'ok':True, 'message':'분석 결과가 삭제되었습니다.'})
