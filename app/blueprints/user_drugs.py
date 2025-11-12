from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.user_drugs import User_drugs
from flask_login import current_user

bp = Blueprint('user_drugs', __name__)

@bp.post('/drugs/<drug_id>')
def add_drugs():

  data = request.get_json()
  user_id = data.get('user_id')
  item_type = data.get('item_type')
  taken_str = data.get('taken', 'false')
  predicted_name = data.get('predicted_name')

  if not user_id or not item_type:
    return jsonify({'error' : '필수 항목을 모두 입력해 주세요.'}), 400
  
  if item_type not in ['medicine', 'supplement']:
    return jsonify({'error': 'item_type은 medicine 또는 supplement여야 합니다.'}), 400

  if taken_str.lower() == 'true':
    taken = True
  else : 
    taken = False

  # DB 저장
  new_drugs = User_drugs(
    user_id=int(user_id),
    item_type = item_type,
    taken = taken,
    predicted_name = predicted_name,
  )
  print(new_drugs)
  db.session.add(new_drugs)
  db.session.commit()
  
  return jsonify({
    'message' : '약 정보 등록 완료',
    'med' : {
      'id' : new_drugs.id,
      'user_id' : new_drugs.user_id,
      'item_type' : new_drugs.item_type,
      'taken' : new_drugs.taken,
      'predicted_name' : new_drugs.predicted_name   
    } 
}), 200

#  put 인식된 약 이름 수정하기 
# @bp.put('putmeds/<int:med_id>')
@bp.put('/meds/<int:med_id>')
def update_meds(med_id):
  data = request.get_json()
  new_name = data.get('confirmed_name')
  print(data)
  print(new_name)

  if not new_name:
    return jsonify({'error' : '수정할 약의 이름을 입력해 주세요.'}), 400

  med = User_drugs.query.get(med_id)

  if not med:
    return jsonify({'error' : '해당 약 정보를 찾지 못했습니다.'}), 400
  
  med.confirmed_name = new_name
  db.session.commit()

  return jsonify({
  'message' : '해당 약 수정이 완료되었습니다.',
  'confirmed_name' : med.confirmed_name    
}), 200


# # get으로 이전에 저장한 약 리스트 불러오기
@bp.get('/drugs/<int:user_id>')
def get_mymeds(user_id):
  meds = User_drugs.query.filter_by(user_id=user_id).all()

  if not meds:
    return jsonify({'error' : '조회된 약이 없습니다.', 'meds' : []}), 400

  meds_List = [{
    'id' : med.id,
    'user_id': med.user_id ,
    'item_type' : med.item_type,
    'taken' : med.taken,
    'predicted_name' : med.predicted_name,
    'confirmed_name' : med.confirmed_name,
    'display_name': med.confirmed_name or med.predicted_name
  } for med in meds]
  
  return jsonify({
    'message' : '조회가 완료되었습니다',
    'med_count' : len(meds_List),
    'meds' : meds_List
    }), 200

#  delete로 다 먹은 약 삭제하기
@bp.delete('/drugs/<int:drug_id>')
def delete_med(drug_id):
  drug = User_drugs.query.get(drug_id)

  if not drug:
    return jsonify({ 'error' : '해당 약을 찾을 수 없습니다'}), 400
  
  if drug.user_id != current_user.id:
    return jsonify({'error': '본인 약만 삭제할 수 있습니다.'}), 403
  
  db.session.delete(drug)
  db.session.commit()

  return jsonify({'message': f'{drug.confirmed_name or drug.predicted_name} (id={drug_id}) 삭제 완료'}), 200