from ..models.user import User
from flask_jwt_extended import create_access_token

# 아이디와 비밀번호로 인증, 성공 시 User 객체를 반환
def authenticate_user(username : str, password: str):
  user = User.query.filter_by(username=username).first()

  if user and user.check_password(password):
    return user
  
  return None

# User 객체로 access_token 생성
def access_token(user):
  # identity,iat,exp는 자동 포함
  # additional_claims : payload를 넣는 공식 매개 변수
  additional_claims = {
    "role": user.role,
  }
  return create_access_token(identity=user.id, additional_claims=additional_claims) # user.id : User 객체 안의 primaryKey값 (DB컬럼)

# user_id로 DB 조회
def get_user_id(user_id): # user_id : user.id값을 전달받거나 저장한 숫자 값 (함수 매개변수)
  return User.query.get(user_id)

# Refresh_token 발급 함수
def refresh_token(user):
  return create_access_token