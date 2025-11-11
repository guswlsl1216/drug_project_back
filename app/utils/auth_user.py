from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

def get_current_user(optional=False):
  """
  JWT 토큰이 있으면 검증 후 user_id 반환.
  optional=True이면 토큰이 없어도 None을 반환하고 통과시킴
  """
  # optional=True 일 때는 로그인 안 해도 통과
  verify_jwt_in_request(optional=optional)

  return get_jwt_identity() # identity 안에 user.id가 있음