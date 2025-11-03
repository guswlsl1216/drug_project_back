# 유효성 검사 관련 로직
from ..models.user import User
import re # 정규표현식을 사용하기 위한 모듈 -> 문자열 패턴을 검사,검색,치환

"""
이메일 형식 검증
r"" -> raw string 역슬래쉬(\)를 특별 처리하지 않고 있는 그대로 사용
@ -> @가 아닌 문자 1개
+ -> 앞 문자가 1개 이상 반복

[^@]+ -> 앞은 아이디, 뒤는 최상위 도메인
@[^@]+ -> 도메인 이름 ( ex : @naver )
\. -> 마침표
"""
def validate_email(email: str):
  errors = []

  # email = email.strip() # 공백 제거

  if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
    errors.append("이메일 형식이 올바르지 않습니다. ex) test@example.com")
  if " " in email:
    errors.append("이메일에 공백을 포함 할 수 없습니다.")

  return errors

# 비밀번호가 8자 이상인지, 문자+숫자 포함 여부 검사
def validate_password(password: str) :
  errors = []
  if len(password) < 8:
    errors.append("비밀번호는 최소 8자 이상이어야 합니다.")
  if not re.search(r"[0-9]", password) :
    errors.append("숫자를 최소 1개 포함해야 합니다.")
  if not re.search(r"[A-Za-z]", password) :
    errors.append("문자를 최소 1개 포함해야 합니다.")
  if re.search(r"\s",password):
    errors.append("비밀번호에 공백은 포함 할 수 없습니다.")
  return errors

# 아이디,이메일,닉네임이 이미 존재하는지 확인
def is_unique_user(username,email,nickname):
  user = User.query.filter(
    (User.username == username) |
    (User.email == email) |
    (User.nickname == nickname)
  ).first() # 첫 번째 것만 조회
  if user is None:
    user = None
  return user  # 조건에 맞는 유저가 없으면 None, 있으면 User 객체를 반환
  