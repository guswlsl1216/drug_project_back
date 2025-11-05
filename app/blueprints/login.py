from flask import Blueprint, request, jsonify, current_app
from ..extensions import db
from ..models.user import User
from ..utils.response import make_response
from flask_jwt_extended import create_access_token

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
    
    user = User.query.filter_by(username=username).first()

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
    
    access_token = create_access_token(identity=user.id)
    
    return make_response(
      ok=True,
      message='로그인 성공하였습니다.',
      data={"access_token": access_token},
      status=200
    )
  
  except Exception as e :
    print(f"[Exception] 로그인 중 오류 발생: {str(e)}")
    db.session.rollback()

    return make_response(
      ok=False,
      message='서버 내부 오류가 발생했습니다.',
      status=500
    )