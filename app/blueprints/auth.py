from flask import Blueprint, request, jsonify
from email_validator import validate_email, EmailNotValidError
from ..extensions import db
from ..models.user import User
from ..utils.db_helpers import safe_commit
from ..utils.response import make_response
from ..utils.validators import validate_email, validate_password, is_unique_user
from flask_jwt_extended import jwt_required, current_user, unset_jwt_cookies
from ..utils.services_auth import authenticate_user

bp = Blueprint('auth',__name__)

@bp.post('/signup')
def signup():
  print("✅ /register route reached")
  try:
    data = request.get_json()
    print("📦 request data:", data)

    username = data.get('username')
    password = data.get('password')
    nickname = data.get('nickname')
    email = data.get('email')
    created_at = data.get('created_at')
    age_str = data.get('age','').strip() # 공백 제거
    age = int(age_str) if age_str.isdigit() else None # 숫자가 아니면 None 처리
    gender = data.get('gender')
    address = data.get('address')
    detail = data.get('detail')
    zipcode = data.get('zipcode')
    tel = data.get('tel')
    role = data.get('role')

    # 필수 입력
    fields = ['username','password','email','nickname']
    missing = [f for f in fields if not data.get(f)]
    if missing:
      return make_response(
        ok=False,
        message=f"필수 항목({', '.join(missing)})을 입력해주세요.",
        status=400
      )
    
    # 이메일 형식 체크
    email_errors = validate_email(email)
    if email_errors:
      return make_response(
        ok=False,
        message=' '.join(email_errors),
        status=400
      )

    # 비밀번호 유효성 체크
    password_errors = validate_password(password)
    if password_errors:
      return make_response(
        ok=False,
        message='비밀번호 조건이 올바르지 않습니다.'+" ".join(password_errors),
        status=400
      )
    
    # 중복 체크
    errors = is_unique_user(username=username, email=email, nickname=nickname)
    if errors:
      print("="*50, errors)
      return make_response(
        ok=False,
        message='이미 가입 된 회원입니다.',
        status=400
      )
    
    # 모델에 만들어 둔 User를 가져와서 여기서 사용 할 user에 넣어줌
    user = User(
      username=username, 
      email=email, 
      nickname=nickname,
      created_at=created_at,
      age=age,
      gender=gender,
      address=address,
      detail=detail,
      zipcode=zipcode,
      tel=tel,
      role=role
    )
    user.set_password(password) # 입력받은 비밀번호를 안전하게 hash해서 저장
    db.session.add(user) # DB에 저장

    # 안전하게 commit
    result = safe_commit({
      'username':'이미 존재하는 아이디입니다.',
      'email': '이미 등록 된 이메일입니다.',
      'nickname':'이미 사용 중인 닉네임입니다.'
    })

    if not result['ok']:
      return make_response(ok=False, message=result['message'], status=400)
    
    return make_response(data=user.to_dict(), ok=True, message='회원가입 완료', status=200)

  except KeyError as e:
    print(f"[KeyError] 회원가입 중 오류 발생 : {str(e)}")
    return make_response(
      ok=False,
      message=f"필드 누락:{e.args[0]}",
      status=400
    )
  except Exception as e:
    print(f"[Exception] 회원가입 중 오류 발생 : {str(e)}")
    db.session.rollback()
    return make_response(
      ok=False,
      message='서버 내부 오류가 발생했습니다.',
      status=500
    )
  
# 회원 비밀번호 재 확인
@bp.post('/user/verify-password')
@jwt_required()
def verify_password():
  user = current_user
  data = request.get_json()
  password = data.get('password')

  if not password:
    return make_response(ok=False, message="비밀번호를 입력해주세요.", status=400)
  
  if user.check_password(password):
    
    return make_response(ok=True, message="비밀번호 확인 완료", status=200)
  
  else:
    return make_response(ok=False, message="비밀번호가 일치하지 않습니다.", status=401)
  
@bp.get('/<int:id>')
@jwt_required()
def info(id):
  user = current_user

  if user.id != id:
    return make_response(ok=False, message="본인의 정보만 조회할 수 있습니다.", status=403)
  
  return make_response(ok=True, message="조회 성공", status=200, data=user.to_dict())

  
  

@bp.post('/user')
@jwt_required()
def update_user():
  user = current_user
  data = request.get_json()

  if not data :
    return make_response(ok=False, message="요청 데이터가 없습니다", status=422)

  # 수정 가능한 필드
  allowed_fields = ['nickname', 'email', 'address','detail','zipcode','tel','password','age','gender']
  
  # 중복 체크 (변경된 경우에만)
  email_for_check = None
  nickname_for_check = None

  # 이메일이 요청에 포함되고, 기존 이메일과 다를 때만 검사
  if 'email' in data and data['email'] != user.email:
      email_for_check = data['email']

  # 닉네임이 요청에 포함되고, 기존 닉네임과 다를 때만 검사
  if 'nickname' in data and data['nickname'] != user.nickname:
      nickname_for_check = data['nickname']

  errors = is_unique_user(
      email=email_for_check,
      nickname=nickname_for_check,
      username=''
  )

  if errors:
    return make_response(ok=False, message="중복 된 정보가 있습니다.", status=400)
  
  update = False

  for filed in allowed_fields:
    if filed in data and data[filed] not in [None,""]:
      if filed == 'password':
        user.set_password(data[filed]) # 비밀번호 변경 시 hash
      elif filed == "age":
        try:
          user.age = int(data[filed])
        except ValueError:
          return make_response(ok=False, message="나이는 숫자만 입력 가능합니다.", status=400)
      else:
        setattr(user, filed, data[filed])
      update = True
  if not update :
    return make_response(ok=False, message="수정 할 내용이 없습니다.", status=400)

  result = safe_commit({
    'email':'이미 등록 된 이메일입니다.',
    'nickname':'이미 사용 중인 닉네임입니다.'
  })

  if not result['ok']:
    return make_response(ok=False, message=result['message'], status=400)

  return make_response(ok=True, message="회원 정보가 업데이트 되었습니다.", data=user.to_dict())

@bp.delete("/delete")
@jwt_required()
def delete():
  user = current_user

  db.session.delete(user)
  db.session.commit()

  response = make_response(ok=True, message="회원 정보가 삭제되었습니다.")
  unset_jwt_cookies(response)

  return response

  