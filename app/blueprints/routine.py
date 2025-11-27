from datetime import datetime
from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import get_current_user, get_jwt_identity, jwt_required, verify_jwt_in_request
from flask_login import current_user, login_required
from app import db
from app.models.routine import Routine
from app.models.routine_log import Routine_log
from app.models.user_meds import User_meds

from sqlalchemy import func
from app.models.auto import get_class
from ..models.user import User
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from ..models.pointHistory import PointHistory, PointTypeEnum

bp = Blueprint('routine', __name__)
SP = get_class("supps_products") 
MP = get_class("meds_products") 

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

def init_scheduler(app):
  scheduler = BackgroundScheduler()
  def accumulate():
    today = (datetime.now() - timedelta(days=1)).date()
    with app.app_context():
      users = db.session.query(User).all()
      for user in users:
        flag = 0
        if not user.routine:
          point = 0
        for routine in user.routine:
          if routine.start_date<=today and routine.end_date>=today:
            flag = 1
            point = 10
            print('-------------포인트 정산-------------')
            print(user.nickname,':',routine)
            routine_log=db.session.query(Routine_log).filter(Routine_log.routine_id==routine.id, Routine_log.date==today).first() 
            if not routine_log or routine_log.count != 'good':
              print('------!!!수행되지않은 루틴!!!-------')
              point = 0
              break
          elif flag==0:
            point = 0
        print(user.nickname,':',point,'점 추가')

        if point > 0:
          current_balance = user.point or 0
          new_balance = current_balance + point

          history = PointHistory(
            user_id = user.id,
            amount = point,                 # 루틴 포인트는 적립이니까 양수
            balance_after = new_balance,    # 이 적립 이후의 최종 잔액
            type = PointTypeEnum.EARN,      # 적립 타입
            description = f"{today} 루틴 달성 포인트",
            routine_date = today    
          )
          db.session.add(history)
          user.point = new_balance
        
        db.session.add(user)
      db.session.commit()
            
      print('-------------포인트 정산완료-------------')
      
  scheduler.add_job(func=accumulate, trigger="cron", hour=0, minute=0)
  scheduler.start()
  # 애플리케이션 종료 시 스케줄러도 종료
  atexit.register(lambda: scheduler.shutdown())
  
#루틴 추가
@bp.post('/addRoutine')
def addRoutine():
  data=request.get_json()
  if not data:
    return jsonify({'ok':False, 'message':'수신오류'}),400
  
  drug_id=data.get('drug_id')

  if drug_id is None:
    # 프론트에서 보내준 사용자가 입력한 복용약 이름을 꺼내옴
    # 테이블 검색, 없으면 추가
    # 그 복용약에 대한 id 생김
    # 그걸 drug_id에 넣음
    med_name = data.get('name')

    if not med_name:
      return jsonify({'ok' : False, 'message' : '복용약 이름 누락'}), 400

    existing_med = User_meds.query.filter_by(med_title=med_name).first()
    
    if existing_med:
      drug_id = existing_med.id
    else:
      new_med = User_meds(med_title=med_name)
      db.session.add(new_med)
      db.session.commit() # commit 하면서 id 생김 
      drug_id = new_med.id
    
  author_id=g.user.id
  drug_id=drug_id
  eattime=data.get('eattime')
  note=data.get('note')
  start_date=data.get('start_date')
  end_date=data.get('end_date')
  count=eattime.count(True)
  
  
  routine = Routine(drug_id=drug_id, author_id=author_id, eattime=eattime, note=note, start_date=start_date, end_date=end_date, count=count)
  db.session.add(routine)
  db.session.commit()      

  return jsonify({'ok':True, 'message':'등록완료'}),200

#루틴 삭제
@bp.delete('/deleteRoutine/<routineId>')
def deleteRoutine(routineId):
  print("============")
  print(routineId, g.user.id)
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
    try:
      eattime=data.get('eattime')
      start_date=data.get('start_date')
      end_date=data.get('end_date')
      note=data.get('note')

      if eattime is not None:
        current_routine.eattime=eattime

      if start_date:
        current_routine.start_date=datetime.strptime(start_date, '%Y-%m-%d').date()
      if end_date:
        current_routine.end_date=datetime.strptime(end_date, '%Y-%m-%d').date()
      
      current_routine.note = note

      db.session.add(current_routine)
      db.session.commit()
      return jsonify({'ok':True, 'message':'수정 완료'}),200
    
    except ValueError as e:
      db.session.rollback()
      return jsonify({'ok' : False, 'message' : f'날짜 형식 오류: {str(e)}'}), 400
    
    except Exception as e:
      db.session.rollback()
      return jsonify({'ok' : False, 'message': f'수정 실패 : {str(e)}'}), 500
  

  return jsonify({'ok':False, 'message':'유저id가 일치하지 않습니다'})


    # current_routine.eattime=eattime
    # current_routine.start_date=start_date
    # current_routine.end_date=end_date
    # current_routine.note=note

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
    logs[routine.id]={}
    counts[routine.id]={}
    if log:
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
  return jsonify({
        'success': True,
        # 프론트엔드가 'medicines' 키를 예상하므로 여기에 데이터를 담습니다.
        'medicines': data 
  })
  
# 약/영양제 유저 id로 한번에 조회하는 기능
@bp.get('/getUserDrugs/<int:user_id>')
def get_user_drugs(user_id):
    """
    유저 루틴 목록 조회
    - SP(영양제), MP(약), User_meds(직접 등록) 모두 포함
    - user_routines 기준으로 처리
    """

    # 1️⃣ 유저 루틴 목록 가져오기
    user_routines = db.session.query(Routine).filter_by(author_id=user_id).all()

    if not user_routines:
        return jsonify({'ok': False, 'message': '등록된 루틴이 없습니다.'})

    result = []

    # 2️⃣ drug_id 기준 분류
    supp_ids = [r.drug_id for r in user_routines if r.drug_id > 100000]  # SP
    med_ids = [r.drug_id for r in user_routines if r.drug_id <= 100000]  # MP + User_meds

    # --- SP(영양제) join ---
    if supp_ids:
        supp_data = (
            db.session.query(Routine, SP)
            .join(SP, Routine.drug_id == SP.id)
            .filter(Routine.author_id == user_id, Routine.drug_id.in_(supp_ids))
            .all()
        )
        for routine, supp in supp_data:
            dayeat = routine.eattime.count(True)
            result.append({
                'id': routine.id,
                'type': 'supplement',
                'drug_id': routine.drug_id,
                'drugName': supp.PRDLST_NM,
                'selectTime' : f'1일 {dayeat}회',
                'method': supp.NTK_MTHD,
                'notice': supp.IFTKN_ATNT_MATR_CN,
                'effect': supp.PRIMARY_FNCLTY,
                'start_date': routine.start_date.strftime('%Y-%m-%d') if routine.start_date else None,
                'end_date': routine.end_date.strftime('%Y-%m-%d') if routine.end_date else None,
                'note': routine.note,
                'eattime': routine.eattime
            })

    # --- MP(기본 약) join ---
    # mp_map = {}
    # if med_ids:
    #     med_data = (
    #         db.session.query(Routine, MP)
    #         .join(MP, Routine.drug_id == MP.id)
    #         .filter(Routine.author_id == user_id, Routine.drug_id.in_(med_ids))
    #         .all()
    #     )
    #     for routine, med in med_data:
    #         mp_map[routine.drug_id] = routine
    #         result.append({
    #             'id': routine.id,
    #             'type': 'medicine',
    #             'drug_id': routine.drug_id,
    #             'drugName': med.ITEM_NAME,
    #             'method': med.UD_DOC_TXT,
    #             'notice': med.NB_DOC_TXT,
    #             'effect': med.EE_DOC_TXT,
    #             'start_date': routine.start_date,
    #             'end_date': routine.end_date,
    #             'note': routine.note,
    #             'eattime': routine.eattime
    #         })

    # --- User_meds(유저 직접 등록 약) join ---
    # user_med_ids = [id_ for id_ in med_ids]
    if med_ids:
        user_meds_data = (
            db.session.query(Routine, User_meds)
            .join(User_meds, Routine.drug_id == User_meds.id)
            .filter(Routine.author_id == user_id, Routine.drug_id.in_(med_ids))
            .all()
        )
        print(user_meds_data)

        for routine, umed in user_meds_data:
            
            dayeat = routine.eattime.count(True)

            result.append({
                'id': routine.id,
                'type': 'user_meds',
                'drug_id': routine.drug_id,
                'drugName': umed.med_title,
                'selectTime' : f'1일 {dayeat}회',
                'method': '',
                'notice': '',
                'effect': '',
                'start_date': routine.start_date.strftime('%Y-%m-%d') if routine.start_date else None,
                'end_date': routine.end_date.strftime('%Y-%m-%d') if routine.end_date else None,
                'note': routine.note,
                'eattime': routine.eattime
            })

    return jsonify({'ok': True, 'drugs': result})

  
# 알약 히스토리 불러오기 달성률...
@bp.get('/getDrugHistory/<int:user_id>')
def get_drug_history(user_id):

  today = date.today()

  # 유저 루틴 목록 조회 
  routines = Routine.query.filter(
    Routine.author_id == user_id,
    Routine.start_date <= today,
    Routine.end_date <= today).all() # 조건 추가 걸기 ( enddate , today 만족하는것만 가져오게 ) 

  if not routines:
    return jsonify({'ok' : False, 'message' : '완료된 루틴이 없습니다.' }), 404
  
  result = []
  total_taken_all = 0
  total_should_take_all = 0

  for r in routines:
    
    total_days = (r.end_date - r.start_date).days + 1 # 복용기간
    total_should_take = total_days * r.count  # 복용기간 동안 먹어야 하는 약 개수 

    # 로그 가져오기 
    logs = Routine_log.query.filter_by(routine_id=r.id).all()

    # 실제 복용 횟수 
    total_taken = 0
    for log in logs:
      for taken in log.performed_times:
        if taken:
          total_taken += 1 
  
    # 루틴 단위 누적
    total_taken_all += total_taken
    total_should_take_all += total_should_take

    # 루틴 별 달성률 계산
    achievement = round((total_taken / total_should_take) * 100, 1) if total_should_take_all > 0 else 0 # 0으로 나눠버리는 경우 방지

    # 약 이름 담아야 함 이름가져오게 join 해서 
    if int(r.drug_id) > 100000:
      drug = db.session.query(SP).filter(SP.id == r.drug_id).first()
      drug_name = drug.PRDLST_NM
    else:
      drug = db.session.query(MP).filter(MP.id == r.drug_id).first()
      drug_name = drug.ITEM_NAME

    # result에 담기 
    result.append({
      'drug_name' : drug_name,
      'period' : f"{r.start_date.strftime('%Y-%m-%d')} ~ {r.end_date.strftime('%Y-%m-%d')}",
      'achievement' : achievement
    })
    # 전체 달성률 
  total_achievement = round((total_taken_all / total_should_take_all) * 100, 1) if total_should_take_all > 0 else 0
    
  return jsonify({
    'ok' : True,
    'history' : result,
    'total_achievement' : total_achievement
  }), 200