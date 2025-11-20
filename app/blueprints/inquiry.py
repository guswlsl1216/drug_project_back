from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.models.inquiry import Inquiry
from ..models.user import User
from app import db
import logging


logger = logging.getLogger(__name__)

bp = Blueprint('inquiry', __name__)

@bp.route('/contact', methods=['post'])
@jwt_required(optional=True)
def submit_inquiry():
  data = {}

  try:
    data = request.get_json(silent=True) or {}
    logger.info(f"Data parsed successfully: {data}")
  except Exception as e:
    logger.error(f"FATAL PARSING ERROR: {e}", exc_info=True)
    return jsonify({'ok':False, 'message':'데이터 파싱 오류. JSON 형식을 확인하세요'}), 400
  
  required_fields = ['name', 'email', 'type', 'title', 'content']

  if not data or not all(data.get(field) and str(data.get(field)).strip() for field in required_fields):
    logger.error(f"Received data: {data}. Missing required fields")
    return jsonify({'ok':False, 'message':'필수 데이터가 누락되었습니다. 프론트엔드 전송 오류'}), 400
  
  logger.info(f"Received Final Data: {data}")

  user = None
  user_id = get_jwt_identity()

  if user_id: # 로그인된 사용자 정보 조회
    try:
      user = User.active_users().filter_by(id=int(user_id)).first()
      if not user:
        logger.warning(f"Active user not found for ID {user_id}")
        return jsonify({'ok':False, 'message':'사용자 인증 정보를 찾을 수 없거나 만료되었습니다. 다시 로그인해 주세요.'}), 401
    except Exception as e:
      logger.error(f"User lookup failed for ID {user_id}: {e}", exc_info=True)
      return jsonify({'ok': False, 'message': '인증된 사용자 정보를 찾을 수 없습니다.'}), 404

  try:
    new_inquiry = Inquiry(
      user_id = user_id,
      name = data['name'],
      email = data['email'],
      type = data['type'],
      title = data['title'],
      content = data['content'],
      created_at = datetime.now(),
      status='pending'
    )

    db.session.add(new_inquiry)
    db.session.commit()

    return jsonify({'ok':True, 'message':'문의가 성공적으로 접수되었습니다.'}), 201
  
  except Exception as e:
    db.session.rollback()
    logger.error(f"Database error: {e}", exc_info=True)
    print(f"문의 접수 중 데이터베이스 오류: {e}")
    return jsonify({'ok':False, 'message':'데이터베이스 저장 오류'}), 500