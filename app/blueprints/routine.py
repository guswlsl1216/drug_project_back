from datetime import datetime
from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import get_current_user, get_jwt_identity, jwt_required, verify_jwt_in_request
from flask_login import current_user, login_required
from app import db
from app.models.routine import Routine
from app.models.routine_log import Routine_log
from app.models.auto import get_class
from ..models.user import User

bp = Blueprint('routine', __name__)

@bp.before_request
def before_api_request():
    
    if request.method == 'OPTIONS':
      return
    
    # JWT 검증을 직접 수행
    try:
        verify_jwt_in_request()
        # get_jwt_identity()로 user_id 가져오기
        current_user_id = get_jwt_identity() 
        
        # 직접 데이터베이스에서 사용자 조회
        g.user = User.query.get(current_user_id)
    except Exception as e:
        print('-----------', e)
        return jsonify({'ok': False, 'message': '인증 실패ㅋㅋ'}), 401

#루틴 추가
@bp.post('/addRoutine')
def addRoutine():
  data=request.get_json()
  if not data:
    return jsonify({'ok':False, 'message':'수신오류'}),400
  
  drug_id=data.get('drug_id')
  author_id=g.user.id

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
  if routine.author_id == g.user.id:
    db.session.delete(routine)
    db.session.commit()
    return jsonify({'ok':True, 'message':'삭제 완료'}),200
  return jsonify({'ok':False, 'message':'유저id가 일치하지 않습니다'})

#루틴 수정
@bp.put('/updateRoutine/<routineId>')
def updateRoutine(routineId):
  data=request.get_json()
  if not data:
    return jsonify({'ok':False, 'message':'수신오류'}),400
  current_routine=db.session.query(Routine).get(routineId)
  if current_routine.author_id == g.user.id:
    eattime=data.get('eattime')
    start_date=data.get('start_date')
    end_date=data.get('end_date')

    current_routine.eattime=eattime
    current_routine.start_date=start_date
    current_routine.end_date=end_date

    db.session.add(current_routine)
    db.session.commit()
    return jsonify({'ok':True, 'message':'수정 완료'}),200
  return jsonify({'ok':False, 'message':'유저id가 일치하지 않습니다'})

#루틴 수행
@bp.post('/performed/<routineId>')
def performed(routineId):
  try:
    data=request.get_json()
    date = data.get('date')
    performed_times = data.get('performed_times')
    routine = Routine.query.filter_by(id=routineId).first()
    print(performed_times.count(True))
    if performed_times.count(True) == 0:
      count='danger'
    elif performed_times.count(True) == routine.count:
      count='good'
    else:
      count='warning'
    
    routine_log = Routine_log.query.filter_by(date=date, routine_id=routineId).first()

    if not routine_log:
      routine_log = Routine_log(routine_id=routineId, date=date, performed_times=performed_times, count=count)
      db.session.add(routine_log)
    else:
      routine_log.performed_times=performed_times
      routine_log.count=count
    
    db.session.commit()
    return jsonify({'ok':True, 'message':'done'}),200
  except Exception as e:
        db.session.rollback()  # 에러 시 롤백
        print("에러에러에러")
        return jsonify({"error": str(e)}), 500

#루틴리스트 불러오기
@bp.get('/getRoutine')
def getRoutine():
  #test current_user.id
  ##################################
  #백레퍼런스로 불러오기
  # user = get_current_user()
  # user_id = user.id
  # routines = user.routine
  ###################################
  user_id = g.user.id
  routine_list=[]
  routines = g.user.routine
  for routine in routines:
    routine_list.append(routine.to_dict())
  
  logs={} #key=routine.id value=log객체
  counts={} #key=routine.id value=count
  for routine in routines:
    log = Routine_log.query.filter(Routine_log.routine_id == routine.id).all()
    if log:
      logs[routine.id]={}
      counts[routine.id]={}
      for i in log:
        date, pr = i.to_dict()
        logs[routine.id][date] = pr
        counts[routine.id][date] = i.count
  return jsonify({'ok':True, 'routine':routine_list, 'log':logs, 'counts':counts}),200

#약/영양제 불러오기
@bp.get('/getDrug/<drugId>')
def getDrug(drugId):
  SP = get_class("supps_products")
  MP = get_class("meds_products")

  if(int(drugId)>100000):
    drug = db.session.query(SP).filter(SP.id == drugId).first()
    return jsonify({'ok':True, 'drugName':drug.PRDLST_NM, 'method':drug.NTK_MTHD, 'notice':drug.IFTKN_ATNT_MATR_CN, 'effect':drug.PRIMARY_FNCLTY})
  else:
    drug = db.session.query(MP).filter(MP.id == drugId).first()
    return jsonify({'ok':True, 'drugName':drug.ITEM_NAME, 'method':drug.UD_DOC_TXT, 'notice':drug.NB_DOC_TXT, 'effect':drug.EE_DOC_TXT})