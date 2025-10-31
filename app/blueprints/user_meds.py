from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.user_meds import User_meds

bp = Blueprint('user_meds', __name__)

@bp.post('/meds')
def add_meds():
  user_id = request.form.get('user_id')
  item_type = request.form.get('item_type')
  taken = request.form.get('taken')
  predicted_name = request.form.get('predicted_name')

  if not user_id or not predicted_name or not item_type or not taken:
    return jsonify({'error' : '필수 항목을 모두 입력해 주세요.'}), 400

  # DB 저장
  new_meds = User_meds(
    user_id=int(user_id),
    item_type = item_type,
    taken = taken,
    predicted_name = predicted_name,
    

  )
  db.session.add(new_meds)
  db.session.commit()

  return jsonify({
    'message' : '이미지 업로드 완료',
    'med' : {
      'id' : new_meds.id,
      'user_id' : new_meds.user_id,
      'predicted_name' : new_meds.predicted_name   
    } 
}), 200

@bp.put('/meds/<int:med_id>')
def update_meds(med_id):
  data = request.get_json()
  new_name = data.get('confirmed_name')

  if not new_name:
    return jsonify({'error' : '수정할 약의 이름을 입력해 주세요.'}), 400

  med = User_meds.query.get(med_id)

  if not med:
    return jsonify({'error' : '해당 약 정보를 찾지 못했습니다.'}), 400
  
  med.confirmed_name = new_name
  db.session.commit()


# # get으로 이전에 저장한 약 리스트 불러오기
@bp.get('/meds/<int:user_id>')
def get_mymeds(user_id):
  meds = User_meds.query.filter_by(user_id=user_id).all()

  if not meds:
    return jsonify({'error' : '조회된 약이 없습니다.', 'meds' : []}), 400

  meds_List = [{
    'id' : med.id,
    'user_id': med.user_id ,
    'predicted_name' : med.predicted_name,
    'confirmed_name' : med.confirmed_name
  } for med in meds]

  print(meds_List)
  return jsonify({
    'message' : '조회가 완료되었습니다',
    'med_count' : len(meds_List),
    'meds' : meds_List
    }), 200

#  put 인식된 약 이름 수정하기 
# @bp.put('putmeds/<int:med_id>')

#  delete로 다 먹은 약 삭제하기