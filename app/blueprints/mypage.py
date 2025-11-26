from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..utils.auth_user import get_current_user
from ..models.order import Order
from ..models.pointHistory import PointHistory, PointTypeEnum

bp = Blueprint('mypage', __name__)

# 내 주문 목록 최신 3개만 불러오기 
@bp.get("/order")
@jwt_required()
def orders_list():
  user_id = int(get_current_user())
  
  orders = (
    Order.query
    .filter_by(user_id = user_id)
    .order_by(Order.payment_at.desc())
    .limit(3)
    .all()
  )

  return jsonify({
    'ok' : True,
    'orders' : [o.to_dict() for o in orders]
  }), 200