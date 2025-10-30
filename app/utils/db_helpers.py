# 데이터베이스 관련 공통 처리 
# 재 사용성 : 회원 가입, 수정, 탈퇴, 계정 복구, 기뷰, 댓글, 장바구니, 주문, 결제 기록 저장 등 재 사용 가능 
from sqlalchemy.exc import IntegrityError
from ..extensions import db 

"""
DB 커밋을 시도하고, 예외 발생 시 자동 롤백처리.
error_messages는 {컬럼명: 에러메세지} 형태의 딕셔너리
"""
def safe_commit(error_messages=None):
  try:
    db.session.commit() # 데이터베이스
    return {'ok':True}
  except IntegrityError as e:
    db.session.rollback() # 예외 발생 시 롤백
    msg = str(e.orig) # e.orig : 원본 DB 예외 객체 -> IntergrityError 안에 들어있는 속성(attribute)

    if error_messages: 
      for field, message in error_messages.items(): 
        if field in msg:
          return {'ok':False, 'message':message}
        
    return {'ok':False, 'message':'데이터베이스 오류가 발생하였습니다.'}