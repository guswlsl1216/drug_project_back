from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from app import db
from app.models.routine import Routine
from app.models.routine_log import Routine_log
from ..models.auto import get_class
from sqlalchemy import func

bp = Blueprint('routine', __name__)
SP = get_class("supps_products") 
MP = get_class("meds_products") 

#루틴 추가
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
  count=eattime.count(True)
  
  routine = Routine(drug_id=drug_id, author_id=author_id, eattime=eattime, start_date=start_date, end_date=end_date, count=count)
  db.session.add(routine)
  db.session.commit()

  return jsonify({'ok':True, 'message':'등록완료'}),200

#루틴 삭제
@bp.delete('/deleteRoutine/<routineId>')
def deleteRoutine(routineId):
  routine=db.session.query(Routine).get(routineId)
  db.session.delete(routine)
  db.session.commit()
  return jsonify({'ok':True, 'message':'삭제 완료'}),200

#루틴 수정
@bp.put('/updateRoutine/<routineId>')
def updateRoutine(routineId):
  data=request.get_json()
  if not data:
    return jsonify({'ok':False, 'message':'수신오류'}),400
  current_routine=db.session.query(Routine).get(routineId)

  eattime=data.get('eattime')
  start_date=data.get('start_date')
  end_date=data.get('end_date')

  current_routine.eattime=eattime
  current_routine.start_date=start_date
  current_routine.end_date=end_date

  db.session.add(current_routine)
  db.session.commit()

  return jsonify({'ok':True, 'message':'수정완료'}),200

#루틴 수행
@bp.post('/performed/<routineId>')
def performed(routineId):
  data=request.get_json()
  date = data.get('date')
  performed_times = data.get('performed_times')

  routine_log = Routine_log.query.filter_by(date=date, routine_id=routineId).first()

  if not routine_log:
    routine_log = Routine_log(routine_id=routineId, date=date, performed_times=performed_times, count=performed_times.count(True))
  else:
    routine_log.performed_times=performed_times
    routine_log.count=performed_times.count(True)
    
  db.session.add(routine_log)
  db.session.commit()
  return jsonify({'ok':True, 'message':'done'}),200

#루틴리스트 불러오기
@bp.get('/getRoutine')
def getRoutine():
  #test current_user.id
  user_id = 1
  routine_list=[]
  routines = Routine.query.filter(Routine.author_id == user_id).all()
  for routine in routines:
    routine_list.append(routine.to_dict())
  
  logs={} #key=routine.id value=log객체
  for routine in routines:
    log = Routine_log.query.filter(Routine_log.routine_id == routine.id).all()
    logs[routine.id]={}
    if log:
      for i in log:
        date, pr = i.to_dict()
        logs[routine.id][date] = pr

  return jsonify({'ok':True, 'routine':routine_list, 'log':logs}),200

# #약/영양제 불러오기
# @bp.get('/getDrug/<drugId>')
# def getDrug(drugId):
#   if(drugId>100000):
#     drug = supps_products


# 복용약/ 영양제 검색 기능 ( 두 가지 구분은 프론트에서 요청할 때 구분할거임 )
@bp.get('/search')
def searchDrug():

  search_name = request.args.get('q', '').strip()
  search_type = request.args.get('type')

  if not search_type or search_type not in ['supps', 'meds']:
    return jsonify({ 'error' : 'type은 반드시 meds 또는 supps 여야 합니다. '}), 400
  
  model = SP if search_type == 'supps' else MP

  normalized_search_name = search_name.replace(' ', '').lower()
  search_keyword = f"%{normalized_search_name}%"

  column_name = model.PRDLST_NM if search_type == 'supps' else model.ITEM_NAME   

  results = (
    db.session.query(model.id, column_name)
    .filter(
      func.lower(func.replace(column_name, ' ', '')).like(search_keyword)
    ).all()
  )

  data = [{ "id" : r[0], "name" : r[1]} for r in results]
  return jsonify(data)
  