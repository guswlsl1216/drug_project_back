from flask import Blueprint, request, jsonify
from email_validator import validate_email, EmailNotValidError
from ..extensions import db
from ..models.user import User
from ..utils.db_helpers import safe_commit
from ..utils.response import make_response
from ..utils.validators import validate_email, validate_password, is_unique_user

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
    updated_at = data.get('updated_at')
    age_str = data.get('age','').strip() # 공백 제거
    age = int(age_str) if age_str.isdigit() else None # 숫자가 아니면 None 처리
    gender = data.get('gender')
    address = data.get('address')
    detailed_address = data.get('detailed_address')
    tel = data.get('tel')

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
      updated_at=updated_at,
      age=age,
      gender=gender,
      address=address,
      detailed_address=detailed_address
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
  
  