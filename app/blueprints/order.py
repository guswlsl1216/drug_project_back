from flask import Blueprint, request, jsonify
from ..extensions import db
from flask_jwt_extended import jwt_required
from ..models.order import Order
from ..models.orderitem import OrderItem
from ..models.user import User
from ..utils.auth_user import get_current_user

bp = Blueprint('orders', __name__)

# 주문자 정보와 동일시 정보 가지고오는 라우트
@bp.get("/user")
@jwt_required()
def order_user_me():
  user_id = get_current_user()

  user = db.session.query(User).get(int(user_id))
  if not user:
    return jsonify({
      "ok" : False,
      "message": "사용자를 찾을 수 없습니다."
    }), 404

  return jsonify({
    "ok" : True,
    "user" : user.to_dict()
  }), 200
