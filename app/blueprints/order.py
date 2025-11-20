from flask import Blueprint, request, jsonify
from ..extensions import db
from flask_jwt_extended import jwt_required
from ..models.order import Order
from ..models.orderitem import OrderItem
from ..models.user import User
from ..models.payment import Payment
from ..utils.auth_user import get_current_user
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from ..models.goods import Goods
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

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

# 기본 배송지 저장하는 라우트
@bp.post("/save")
@jwt_required()
def save_address():
  user_id = get_current_user()

  data = request.get_json()

  zipcode = data.get("zipcode", "")
  address = data.get("address", "")
  address_detail = data.get("address_detail", "")

  user = db.session.query(User).get(int(user_id))

  if not user:
    return jsonify({"ok": False, "message": "사용자를 찾을 수 없습니다."}), 404
  
  user.zipcode = zipcode
  user.address = address
  user.detailed_address = address_detail

  try:
    db.session.commit()
  except Exception as e:
    db.session.rollback()
    return jsonify({"ok": False, "message": f"배송지 저장 실패: {e}"}), 500

  return jsonify({"ok": True}), 200

# 내 주문 목록
@bp.get("/me")
@jwt_required()
def orders_list():
  page = request.args.get('page', type=int, default=1)
  per_page = request.args.get("per_page", 10, type=int)
  range_type = request.args.get("range") # 1m / 3m / 6m / all
  keyword = request.args.get("keyword", "").strip()

  now = datetime.now()
  start_dt = None
  end_dt = None

  # 최근 1개월
  if range_type == "1m":
    start_dt = now - relativedelta(months=1)
  # 최근 3개월
  elif range_type == "3m":
    start_dt = now - relativedelta(months=3)
  # 최근 6개월
  elif range_type == "6m":
    start_dt = now - relativedelta(months=6)

  elif range_type == "all":
    pass

  if end_dt is None and range_type in ("1m", "3m", "6m"):
    end_dt = now

  user_id = int(get_current_user())
  orders_q = ( 
    db.session.query(Order)
    .options(joinedload(Order.orderitems).joinedload(OrderItem.goods)) # 상품명 검색 위해 joinload 
    .filter(Order.user_id == user_id)
  )

  if start_dt:
    orders_q = orders_q.filter(Order.payment_at >= start_dt)
  
  if end_dt:
    orders_q = orders_q.filter(Order.payment_at <= end_dt)

  if keyword:
    orders_q = orders_q.filter( 
      or_(
        Order.order_code.ilike(f"%{keyword}%"),        # 주문번호 검색 
        Order.orderitems.any(                         # OrderItem → Goods
          OrderItem.goods.has(Goods.goods_name.ilike(f"%{keyword}%"))
        )
      )
    )

  orders_q = orders_q.order_by(Order.payment_at.desc())
  pagination = orders_q.paginate(page=page, per_page=per_page, error_out=False) # type: ignore[attr-defined]

  return jsonify({
    'ok' : True,
    'orders' : [o.to_dict() for o in pagination.items],
    'total' : pagination.total,
    'page' : pagination.page,
    'pages' : pagination.pages,
    "per_page": per_page
  }), 200

# 주문 상세
@bp.get("/<int:id>")
@jwt_required()
def order_detail(id):
  user_id = int(get_current_user())
  order = db.session.query(Order).filter_by(id=id, user_id=user_id).first()

  if not order:
    return jsonify({"ok": False, "message": "주문내역을 찾을 수 없습니다."}), 404
  
  payment = (
    db.session.query(Payment)
    .filter_by(orders_id=id, user_id=user_id)
    .order_by(Payment.created_at.desc())
    .first()
  )

  data = order.to_dict()

  if payment:
    data["payment"] = {
      "id": payment.id,
      "method": payment.method,   # 카드 / 가상계좌 / 간편결제 ...
      "type": payment.type,       # NORMAL / BILLING / BRANDPAY
      "status": payment.status,   # READY / DONE / CANCELED ...
      "amount": payment.amount,
      "paid_at": payment.paid_at,
      "receipt_url": payment.receipt_url,
    }
  else:
    data["payment"] = None
  
  return jsonify({
    "ok" : True,
    "order" : data
  }), 200

@bp.get("/addresses")
@jwt_required()
def get_order_addresses():
  user_id = get_current_user()
  if not user_id:
    return jsonify({"ok" : False, "message": "로그인이 필요합니다."}), 401
  
  orders = (
    Order.query
      .filter_by(user_id=user_id)
      .filter(Order.status == "PAID")
      .order_by(Order.payment_at.desc())
      .all()
  )

  seen = set()
  addresses = []

  for o in orders:
    key = (o.receiver, o.phone, o.zipcode, o.address, o.address_detail)
    if key in seen:
      continue
    seen.add(key)

    addresses.append({
      "receiver": o.receiver,
      "phone" : o.phone,
      "zipcode" : o.zipcode,
      "address" : o.address,
      "address_detail" : o.address_detail
    })

    if len(addresses) >= 10:  # 최대 10개 정도만
      break

  return jsonify({
    "ok" : True,
    "addresses" : addresses
  }), 200