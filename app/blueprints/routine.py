from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from app import db
from app.models.routine import Routine

bp = Blueprint('routine', __name__)

#루틴추가
@bp.post('/addRoutine')
def addRoutine():
  data=request.get_json()
  if not data:
    return jsonify({'ok':False, 'message':'수신오류'}),400
  #drugName = data.get('drugName')
  #drug = db.session.query(drug).get(drugName)
  #drug_id=drug.drug_id
  
  #Postman Test drug_id author_id
  drug_id=data.get('drug_id')
  author_id=data.get('author_id')

  eattime=data.get('eattime')
  start_date=data.get('start_date')
  end_date=data.get('end_date')
  count=data.get('count')
  
  routine = Routine(drug_id=drug_id, author_id=author_id, eattime=eattime, start_date=start_date, end_date=end_date, count=count)
  db.session.add(routine)
  db.session.commit()

  return jsonify({'ok':True, 'message':'등록완료'}),200

#루틴삭제
@bp.delete('/deleteRoutine/<routineId>')
def deleteRoutine(routineId):
  routine=db.session.query(Routine).get(routineId)
  db.session.delete(routine)
  db.session.commit()
  return jsonify({'ok':True, 'message':'삭제 완료'}),200

#루틴수정
@bp.put('/updateRoutine/<routineId>')
def updateRoutine(routineId):
  data=request.get_json()
  if not data:
    return jsonify({'ok':False, 'message':'수신오류'}),400
  current_routine=db.session.query(Routine).get(routineId)
  
  #drugName = data.get('drugName')
  #drug = db.session.query(drug).get(drugName)
  #drug_id=drug.drug_id
  
  #Postman Test drug_id
  drug_id=data.get('drug_id')

  eattime=data.get('eattime')
  start_date=data.get('start_date')
  end_date=data.get('end_date')
  count=data.get('count')

  current_routine.drug_id=drug_id
  current_routine.eattime=eattime
  current_routine.start_date=start_date
  current_routine.end_date=end_date
  current_routine.count=count

  db.session.add(current_routine)
  db.session.commit()

  return jsonify({'ok':True, 'message':'수정완료'}),200