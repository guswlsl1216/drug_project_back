from flask import Blueprint, request, jsonify, make_response as flask_make_response
from ..extensions import db
from ..models.user import User
from ..utils.response import make_response
from ..utils.services_auth import authenticate_user, user_access_token, user_refresh_token
from flask_jwt_extended import jwt_required, unset_jwt_cookies, get_jwt_identity, set_access_cookies, set_refresh_cookies, verify_jwt_in_request

bp = Blueprint('login',__name__)

@bp.post('/login')
def login():
  
 
  try:
    data = request.get_json()
   
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
      return make_response(
        ok=False,
        message='아이디와 비밀번호를 입력해주세요.',
        status=400
      )
    
    user = authenticate_user(username, password)

    if not user:
      return make_response(
        ok=False,
        message='존재하지 않는 사용자입니다.',
        status=400
      )
    
    if user.deleted_at is not None: # 탈퇴가 None이 아닌 유저(탈퇴를 누름)
      return make_response(
        ok=False,
        message='이미 탈퇴한 사용자입니다.',
        status=400
      )
    
    if user and not user.check_password(password):
      return make_response(
        ok=False,
        message='아이디 또는 비밀번호가 일치하지 않습니다.',
        status=400
      )
    
    access_token = user_access_token(user)
    refresh_token = user_refresh_token(user)

    user_info = {
      "id":user.id,
      "nickname":user.nickname,
      "email":user.email,
      "tel":user.tel
    }
    
    res = flask_make_response(jsonify({
      'ok':True,
      'message':'로그인 성공하였습니다.',
      "data":user_info
    }), 200 )
    

    # 쿠키에 토큰 저장
    set_access_cookies(res, access_token)
    set_refresh_cookies(res, refresh_token)


    return res
  
  except Exception as e :
    print(f"[Exception] 로그인 중 오류 발생: {str(e)}")
    db.session.rollback()

    return make_response(
      ok=False,
      message='서버 내부 오류가 발생했습니다.',
      status=500
    )
  
@bp.post("/refresh")
@jwt_required(refresh=True) # refresh_token 검증
def refresh():
  user_id = get_jwt_identity()
  user = User.query.get(user_id)
  new_access_token = user_access_token(user)

  res = make_response(
    ok=True,
    message='Access Token 갱신 완료',
    status=200
  )
  set_access_cookies(res, new_access_token) # 쿠키에 새 accessToken 저장
  return res

@jwt_required()
@bp.get("/check")
def login_check():
  try:
    verify_jwt_in_request() # cookie에서 JWT 확인
    user_id = get_jwt_identity()
    return jsonify(logged_in=True, user=user_id)
  except Exception:
    return jsonify(logged_in=False)

@bp.post("/logout")
def logout():
  res = make_response(ok=True, message="로그아웃 되었습니다.")
  unset_jwt_cookies(res) # JWT 쿠키를 제거
  return res