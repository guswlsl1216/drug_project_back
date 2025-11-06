from ..models.user import User
from flask_jwt_extended import create_access_token, create_refresh_token

# 아이디와 비밀번호로 인증, 성공 시 User 객체를 반환
def authenticate_user(username : str, password: str):
  user = User.query.filter_by(username=username).first()

  if user and user.check_password(password):
    return user
  
  return None

# User 객체로 access_token 생성
def user_access_token(user):
  # identity,iat,exp는 자동 포함
  # additional_claims : payload를 넣는 공식 매개 변수
  additional_claims = {
    "role": user.role,
  }
  return create_access_token(identity=user.id, additional_claims=additional_claims) # user.id : User 객체 안의 primaryKey값 (DB컬럼)

# Access Token 발급 (JWT, identity에 user.id 사용)
def user_access_token(user): 
  return create_access_token(identity=str(user.id))

# Refresh Token 발급 (JWT, identity에 user.id 사용)
def user_refresh_token(user):
  return create_refresh_token(identity=str(user.id))

