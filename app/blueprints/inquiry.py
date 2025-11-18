from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.models.inquiry import Inquiry
from ..models.user import User
from app import db

bp = Blueprint('inquiry', __name__)

@bp.route('/contact', methods=['post'])
@jwt_required(optional=True)
def submit_inquiry():
  data = request.get_json()
  user_id = get_jwt_identity()
  user = None

  if user_id:
    user = User.active_users().filter_by(id=user_id).first()

  final_name = data.get('name') if data.get('name') else (user.nickname if user else None)
  final_email = data.get('email') if data.get('email') else (user.email if user else None)

  required_fields = ['type', 'title', 'content']

  if not final_name or not final_email:
    return jsonify({'ok':False, 'message': '문의자 이름과 이메일은 필수 입력 항목입니다.'}), 400
  
  for field in required_fields:
    if not data.get(field):
      return jsonify({'ok':False, 'message':f'필수 입력 항목({field})이 누락되었습니다.'}), 400
    
  try:
    new_inquiry = Inquiry(
      user_id = user.id if user else None,
      name = final_name,
      email = final_email,
      type = data['type'],
      title = data['title'],
      content = data['content'],
      created_at = datetime.now()
    )

    db.session.add(new_inquiry)
    db.session.commit()

    return jsonify({'ok':True, 'message':'문의가 성공적으로 접수되었습니다.'}), 201
  
  except Exception as e:
    db.session.rollback()
    print(f"문의 접수 중 데이터베이스 오류: {e}")
    return jsonify({'ok':False, 'message':'서버 오류로 문의 접수에 실패했습니다.'}), 500