from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.goods import Goods
from flask_jwt_extended import jwt_required
from ..utils.auth_user import get_current_user
from ..models.orderitem import OrderItem
from ..models.cart import Cart
from ..models.payment import Payment
from ..models.order import Order
from ..models.user import User
from ..models.qna import QnA
from ..models.inquiry import Inquiry
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from datetime import datetime
from ..utils.decorators import admin_required

bp = Blueprint('admin', __name__)

# 상품 등록
@bp.post('/goods')
@jwt_required()
@admin_required
def write_goods():
  data = request.get_json()

  category = data.get('category')
  classify = data.get('classify')
  goods_name = data.get('goods_name')
  goods_desc = data.get('goods_desc')
  image_path = data.get('image_path')
  is_active = bool(data.get('is_active', True))

  # 2) 숫자 파싱은 try/except로 안전하게
  def parse_int(val, default=None):
    if val is None or val == '':
      return default
    try:
      return int(val)
    except (TypeError, ValueError):
      return default
    
  price = parse_int(data.get('price'), default=None)
  stock = parse_int(data.get('stock'), default=None)

  missing = []
  if not category: missing.append("카테고리")
  if not classify: missing.append("분류")
  if not goods_name: missing.append("상품명")
  if goods_desc is None or goods_desc == "": missing.append("상품 설명")
  if price is None: missing.append("가격")
  if stock is None: missing.append("재고")
  if not image_path: missing.append("대표 이미지")

  if missing:
    return jsonify({
      "ok" : False,
      "message" : f"필수 항목 누락 : {','.join(missing)} "
    }), 400
  
  #(권장) HTML sanitize
  from ..utils.sanitize import sanitize_html
  goods_desc = sanitize_html(goods_desc)

  user_id = get_current_user()

  goods = Goods(
    category=category,
    classify=classify,
    goods_name=goods_name,
    goods_desc=goods_desc,
    price=price,
    stock=stock,
    image_path=image_path,
    is_active=is_active,
    user_id=user_id
  )

  db.session.add(goods)

  try:
    db.session.commit()
  except Exception as e:
    db.session.rollback()
    return jsonify({'ok' : False, 'message' : f'상품 등록 실패: {e}'}), 500
  
  return jsonify({
    "ok" : True,
    "message" : "상품이 등록되었습니다.",
    "goods" : goods.to_dict()
  }), 201

# 상품 이미지 등록
@bp.post('/upload')
@jwt_required()
@admin_required
def image_upload():
  from flask import current_app, url_for
  from werkzeug.utils import secure_filename
  import os, uuid

  try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
  except Exception:
    PIL_AVAILABLE = False

  ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

  def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT
  
  file = request.files.get('image') or request.files.get('file')
  if not file or file.filename == "":
    return jsonify({"ok": False, "message": "파일이 없습니다."}), 400
  
  # 확장자 체크
  if not allowed_file(file.filename): # type: ignore
    return jsonify({"ok": False, "message": "허용되지 않은 파일 형식입니다 (png, jpg, jpeg, gif, webp)."}), 400
  
  upload_subdir = current_app.config.get("UPLOAD_SUBDIR", "uploads")
  upload_dir = os.path.join(current_app.static_folder, upload_subdir) # type: ignore
  os.makedirs(upload_dir, exist_ok=True)

  original = secure_filename(file.filename) # type: ignore
  _, ext = os.path.splitext(original)
  ext = (ext or ".jpg").lower()
  filename = f"{uuid.uuid4().hex}{ext}"
  save_path = os.path.join(upload_dir, filename)

  # (선택) 이미지 유효성 검증
  if PIL_AVAILABLE:
    try:
      file.stream.seek(0)
      img = PILImage.open(file.stream)
      img.verify()  # 이미지 포맷 검증
      file.stream.seek(0)  # 저장 전에 스트림 되감기
    except Exception:
      return jsonify({"ok": False, "message": "이미지 파일이 손상되었거나 형식이 올바르지 않습니다."}), 400

  # 저장
  file.save(save_path)

  # 절대 URL (http://localhost:5000/static/uploads/xxx.jpg)
  absolute_url = url_for('static', filename=f"{upload_subdir}/{filename}", _external=True)

  # 브라우저에서 접근 가능한 공개 경로 (/static/uploads/파일명)
  public_url = f"/static/{upload_subdir}/{filename}"

  return jsonify({
    "ok": True,
    "message": "이미지 업로드 완료",
    "image_path": public_url,  # 프론트에서 사용
    "url": absolute_url,          # 혹시 다른 키를 참고해도 되게 중복 제공
    "filename": filename
  }), 200

@bp.get('/goods/<int:id>')
@jwt_required()
def get_goods(id):
  goods = db.session.query(Goods).get(id)

  if not goods:
    return jsonify({'ok' : False, 'message' : '상품을 찾을 수 없습니다.'}), 404
  
  return jsonify({'ok' : True, 'goods' : goods.to_dict()}), 200

# 상품 수정
@bp.put("/edit/<int:id>")
@jwt_required()
@admin_required
def edit_goods(id):
  data = request.get_json()

  category = data.get('category')
  classify = data.get('classify')
  goods_name = data.get('goods_name')
  goods_desc = data.get('goods_desc')
  image_path = data.get('image_path')
  is_active = bool(data.get('is_active', True))

  def parse_int(val, default=None):
    if val is None or val == '':
      return default
    try:
      return int(val)
    except (TypeError, ValueError):
      return default

  price = parse_int(data.get('price'), default=None)
  stock = parse_int(data.get('stock'), default=None)

  missing = []
  if not category: missing.append("카테고리")
  if not classify: missing.append("분류")
  if not goods_name: missing.append("상품명")
  if goods_desc is None or goods_desc == "": missing.append("상품 설명")
  if price is None: missing.append("가격")
  if stock is None: missing.append("재고")
  if not image_path: missing.append("대표 이미지")

  if missing:
    return jsonify({
      "ok" : False,
      "message" : f"수정 필수 항목 누락 : {','.join(missing)} "
    }), 400
  
  from ..utils.sanitize import sanitize_html
  goods_desc = sanitize_html(goods_desc)
  
  goods = db.session.query(Goods).get(id)

  user_id = get_current_user()

  try:
    user_id = int(user_id)
  except Exception:
    user_id = None

  if not goods:
    return jsonify({'ok': False, 'message': '상품을 찾을 수 없습니다.'}), 404
  
  if goods.user_id != user_id:
    return jsonify({'ok' : False, 'message' : '작성자만 수정 가능합니다'}), 403
  
  goods.category = category
  goods.classify = classify
  goods.price = price
  goods.goods_name = goods_name
  goods.goods_desc = goods_desc
  goods.stock = stock
  goods.image_path = image_path
  goods.is_active = is_active

  db.session.add(goods)

  try:
    db.session.commit()
  except Exception:
    db.session.rollback()
    return jsonify({'ok' : False, 'message' : '상품 수정 실패.'}), 500
  
  return jsonify({'ok' : True, 'message' : '상품 수정 완료', 'goods': goods.to_dict()}), 200

# 상품 삭제
@bp.delete("/goods/<int:id>")
@jwt_required()
@admin_required
def delete_goods(id):
  goods = db.session.query(Goods).get(id)

  user_id = get_current_user()

  try:
    user_id = int(user_id)
  except Exception:
    user_id = None

  if not goods:
    return jsonify({'ok': False, 'message': '상품을 찾을 수 없습니다.'}), 404
  
  if goods.user_id != user_id:
    return jsonify({'ok' : False, 'message' : '작성자만 삭제 가능합니다'}), 403
  
  from sqlalchemy import func
  order_count = (db.session.query(func.count(OrderItem.id))
                .filter(OrderItem.goods_id == id)
                .scalar())
  
  try:
      # 재고 0 → 판매중지 처리
      if goods.stock <= 0:
        goods.is_active = False
        Cart.query.filter_by(goods_id=id).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'ok': True, 'message': '재고가 없어서 판매 중지 처리했습니다.'}), 200
        
      #  주문 이력 → 삭제 불가 → 판매중지
      if order_count > 0:
        goods.is_active = False
        Cart.query.filter_by(goods_id=id).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'ok': True, 'message': '주문 이력이 있어 판매 중지 처리했습니다.'}), 200
        
      # 주문 이력 없고 재고도 정상 → 완전 삭제
      db.session.delete(goods)
      db.session.commit()
      return jsonify({'ok': True, 'message': '상품 삭제 완료'}), 200
  except Exception:
    db.session.rollback()
    return jsonify({'ok' : False, 'message' : '상품 삭제 처리에 실패했습니다.'}), 500
  
# 품절 상품
@bp.get("/goods/soldout")
@jwt_required()
def get_soldout_goods():
  user_id = get_current_user()
  user = db.session.query(User).get(user_id)
  if not user or user.role != "admin":
    return jsonify({"ok": False, "message": "관리자만 조회할 수 있습니다."}), 403
  
  page = request.args.get("page", type=int, default=1)
  per_page = 10

  goods_q = Goods.query.filter(
    (Goods.stock <= 0) | (Goods.is_active == False)  # type: ignore[operator]
  )

  pagination = goods_q.paginate(page=page, per_page=per_page)
  goods = [g.to_dict() for g in pagination.items]

  return jsonify({
    "ok": True,
    "goods": goods,
    "page": pagination.page,
    "pages": pagination.pages,
    "total": pagination.total,
    "per_page": per_page
  }), 200

# 품절 상품 재고 수정
@bp.put("/goods/<int:id>/stock")
@jwt_required()
@admin_required
def soldout_goods_edit(id):
  data = request.get_json()
  stock = data.get("stock")

  if stock is None:
    return jsonify({"ok": False, "message": "stock 값이 필요합니다."}), 400
  
  try:
    stock = int(stock)
  except ValueError:
    return jsonify({"ok": False, "message": "stock 값은 숫자만 가능합니다."}), 400

  goods = Goods.query.get(id)

  if not goods:
    return jsonify({'ok': False, 'message': '상품을 찾을 수 없습니다.'}), 404

  goods.stock = stock

  if stock > 0:
    goods.is_active = True
  else:
      goods.is_active = False

  try:
    db.session.commit()
  except Exception:
    db.session.rollback()
    return jsonify({'ok' : False, 'message' : '재고 수정 실패.'}), 500
  
  return jsonify({"ok" : True, "message": "재고가 수정되었습니다.", "stock": stock}), 200

# 상품 리스트
@bp.get('/goods')
@jwt_required()
@admin_required
def board_list():
  page = request.args.get('page', type=int, default=1)
  per_page = request.args.get("per_page", 10, type=int)
  goods_q = Goods.query.order_by(Goods.create_at.desc())
  pagination = goods_q.paginate(page=page , per_page=per_page)

  
  return jsonify({
    'ok' : True,
    'goods' : [g.to_dict() for g in pagination.items],
    'total' : pagination.total,
    'page' : pagination.page,
    'pages' : pagination.pages,
    "per_page": per_page
  }), 200
  
@bp.get('/payments')
@jwt_required()
@admin_required
def payments_list():
  page = request.args.get('page', type=int, default=1)
  per_page = request.args.get("per_page", 10, type=int)

  status = request.args.get("status")
  method = request.args.get("method")
  query = request.args.get("query")

  payment_q = Payment.query.join(User).order_by(Payment.created_at.desc())

  # 결제 상태 필터
  if status:
    payment_q = payment_q.filter(Payment.status == status)
  
  # 결제 방법 필터
  if method:
    payment_q = payment_q.filter(Payment.method == method)

  # 검색어 (주문번호 OR 주문자명)
  if query:
    # .isdigit() : 모든 문자가 숫자이면 True, 하나라도 숫자가 아닌 문자가 포함되어 있으면 False를 반환
    if query.isdigit():
      # 숫자 → 주문ID 검색
      payment_q = payment_q.filter(Payment.orders_id == int(query))
    else:
      # 문자열 → 유저 닉네임 검색
      payment_q = payment_q.filter(User.nickname.like(f"%{query}%"))

  pagination = payment_q.paginate(page=page, per_page=per_page)
  approved_sum = (
    db.session.query(func.coalesce(func.sum(Payment.amount), 0))
    .filter(Payment.status == "DONE")
    .scalar()
  )
  cancelled_sum = (
    db.session.query(func.coalesce(func.sum(Payment.amount), 0))
    .filter(Payment.status.in_(["CANCELED", "PARTIAL_CANCELED"]))
    .scalar()
  )
  
  refunded_sum = cancelled_sum

  return jsonify({
    "ok" : True,
    'payments': [p.to_dict() for p in pagination.items],
    'total' : pagination.total,
    'page' : pagination.page,
    'pages' : pagination.pages,
    'per_page': per_page,
    'approved_sum' : approved_sum,
    'cancelled_sum' : cancelled_sum,
    'refunded_sum' : refunded_sum
  }), 200

@bp.get('/orders/<int:orders_id>')
@jwt_required()
@admin_required
def orderDetali(orders_id):
  order = db.session.query(Order).get(orders_id)

  if not order:
    return jsonify({'ok' : False, 'message' : '주문 내역을 찾을 수 없습니다.'}), 404
  
  # 주문 아이템 목록 + Goods 미리 로드
  items = (
    db.session.query(OrderItem) # OrderItem 테이블 기준으로 쿼리
    .options(selectinload(OrderItem.goods)) # type: ignore[operator] , 관련된 Goods들 한 번에 로드
    .filter(OrderItem.orders_id == orders_id) # 이 주문에 속한 아이템들만 필터링.
    .all()
  )

  # 응답 조립
  data = order.to_dict()
  
  data["items"] = [{
    "goods_id": it.goods_id,
    "goods_name": getattr(it.goods, "goods_name", None),
    "image": getattr(it.goods, "image_path", None),
    "unit_price": it.unit_price,
    "count": it.count,
    "subtotal": it.subtotal,
  } for it in items]
  
  return jsonify({'ok' : True, 'order' : data}), 200


@bp.get('/qna')
@jwt_required()
@admin_required
def qna_list():
  page = request.args.get('page', type=int, default=1)
  per_page = request.args.get("per_page", 10, type=int)

  status = request.args.get("status")
  query = request.args.get("query")

  qna_q = QnA.query.join(User, QnA.user_id == User.id).order_by(QnA.created_at.desc())

  # 문의 상태 필터 (pending / answered 등)
  if status:
    qna_q = qna_q.filter(QnA.status == status)
  
  # 검색어 (상품번호 OR 문의자명)
  if query:
    # .isdigit() : 모든 문자가 숫자이면 True, 하나라도 숫자가 아닌 문자가 포함되어 있으면 False를 반환
    if query.isdigit():
      # 숫자 → 상품 ID 검색
      qna_q = qna_q.filter(QnA.goods_id == int(query))
    else:
      # 문자열 → 유저 닉네임 검색
      qna_q = qna_q.filter(User.nickname.like(f"%{query}%"))

  pagination = qna_q.paginate(page=page, per_page=per_page)

  return jsonify({
    'ok' : True,
    'qna': [q.admin_to_dict() for q in pagination.items],
    'total' : pagination.total,
    'page' : pagination.page,
    'pages' : pagination.pages,
    'per_page': per_page
  }), 200

@bp.post('/qna/<int:id>')
@jwt_required()
@admin_required
def answer_inquiry(id):
  data = request.get_json()
  answer = data.get("answer")

  if not answer:
    return jsonify({"ok" : False, "message" : "답변 내용을 입력해주세요."}), 400

  qna = db.session.query(QnA).get(id)
  if not qna:
    return jsonify({"ok":False, "message" : "문의 내역을 찾을 수 없습니다."}), 404
  
  user_id = get_current_user()
  
  qna.admin_id = user_id
  qna.answer_content = answer
  qna.status = "answered"
  qna.answered_at = datetime.now()

  try:
    db.session.commit()
  except Exception:
    db.session.rollback()
    return jsonify({'ok' : False, 'message' : '답변 등록 실패.'}), 500

  return jsonify({
    "ok" : True,
    "message" : "답변이 등록되었습니다."
  }), 200

@bp.get('/inquiry')
@jwt_required()
@admin_required
def inquiry_list():
  page = request.args.get('page', type=int, default=1)
  per_page = request.args.get("per_page", 10, type=int)

  status = request.args.get("status")
  query = request.args.get("query")

  inquiry_q = Inquiry.query.order_by(Inquiry.created_at.desc())

  # 문의 상태 필터 (pending / answered 등)
  if status:
    inquiry_q = inquiry_q.filter(Inquiry.status == status)
  
  # 검색어 (상품번호 OR 문의자명)
  if query:
    inquiry_q = inquiry_q.filter(
      (Inquiry.name.like(f"%{query}%")) |
      (Inquiry.email.like(f"%{query}%"))
    )

  pagination = inquiry_q.paginate(page=page, per_page=per_page)

  return jsonify({
    'ok' : True,
    'inquiries': [i.to_dict() for i in pagination.items],
    'total' : pagination.total,
    'page' : pagination.page,
    'pages' : pagination.pages,
    'per_page': per_page
  }), 200