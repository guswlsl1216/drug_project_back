from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..utils.auth_user import get_current_user
from ..models.order import Order
from ..models.pointHistory import PointHistory
from ..models.user import User

bp = Blueprint('mypage', __name__)

# 내 주문 목록 최신 3개만 불러오기 
@bp.get("/order")
@jwt_required()
def orders_list():

  user_id = int(get_current_user())
  
  orders = (
    Order.query
    .filter_by(user_id = user_id)
    .filter(Order.update_at.isnot(None))     # 결제 완료된 주문만
    .order_by(Order.payment_at.desc())
    .limit(3)
    .all()
  )

  return jsonify({
    'ok' : True,
    'orders' : [o.to_summary_dict() for o in orders]
  }), 200

# 포인트 적립 목록
@bp.get("/point")
@jwt_required()
def point_list():
  user_id = int(get_current_user())
  user = User.query.filter_by(id = user_id).first()

  if not user:
    return jsonify({"ok" : False, "message" : "유저 정보를 찾을 수 없습니다."}), 401
  

  page = request.args.get('page', type=int, default=1)
  per_page = request.args.get("per_page", 20, type=int)

  point_q = (
    PointHistory.query
    .filter_by(user_id = user_id)
    .order_by(PointHistory.created_at.desc())
  )

  pagination = point_q.paginate(page=page , per_page=per_page)
  histories = [p.to_dict() for p in pagination.items]

  return jsonify({
    "ok" : True,
    "point" : user.point or 0,
    "histories" : histories,
    'total' : pagination.total,
    'page' : pagination.page,
    'pages' : pagination.pages,
    "per_page": per_page
  }), 200