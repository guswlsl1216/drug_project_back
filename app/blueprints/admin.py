from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..extensions import db
from ..models.goods import Goods

bp = Blueprint('admin', __name__)

# 상품 등록
@bp.post('/goods')
def write_goods():
  data = request.get_json()

  category = data.get('category')
  classify = data.get('classify')
  price = int(data.get('price', 0))
  goods_name = data.get('goods_name')
  goods_desc = data.get('goods_desc')
  stock = int(data.get('stock', 0))
  image_path = data.get('image_path')
  is_active = bool(data.get('is_active', True))

  missing = []
  if not category: missing.append("카테고리")
  if not classify: missing.append("분류")
  if not goods_name: missing.append("상품명")
  if not goods_desc: missing.append("상품 설명")
  if not price: missing.append("가격")
  if not stock: missing.append("재고")

  if missing:
    return jsonify({
      "ok" : False,
      "message" : f"필수 항목 누락 : {','.join(missing)} "
    }), 400
  
  goods = Goods(
    category=category,
    classify=classify,
    goods_name=goods_name,
    goods_desc=goods_desc,
    price=price,
    stock=stock,
    image_path=image_path,
    is_active=is_active,
    user_id=current_user.id
  )

  db.session.add(goods)

  try:
    db.session.commit()
  except Exception:
    db.session.rollback()
    return jsonify({'ok' : False, 'message' : '상품 등록 실패.'}), 500
  
  return jsonify({
    "ok" : True,
    "message" : "상품이 등록되었습니다.",
    "goods" : goods.to_dict()
  })

# 상품 이미지 등록
@bp.post('/upload')
def image_upload():
  from flask import current_app
  from werkzeug.utils import secure_filename
  import os, uuid

  try:
    from PIL import Image
    PIL_AVAILABLE = True
  except Exception:
    PIL_AVAILABLE = False

  ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

  def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT
  
  file = request.files.get('file')
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
      img = Image.open(file.stream)
      img.verify()  # 이미지 포맷 검증
      file.stream.seek(0)  # 저장 전에 스트림 되감기
    except Exception:
      return jsonify({"ok": False, "message": "이미지 파일이 손상되었거나 형식이 올바르지 않습니다."}), 400

  # 저장
  file.save(save_path)

  # 브라우저에서 접근 가능한 공개 경로 (/static/uploads/파일명)
  public_url = f"/static/{upload_subdir}/{filename}"

  return jsonify({
    "ok": True,
    "message": "이미지 업로드 완료",
    "image_path": public_url,  # 프론트에서 사용
    "url": public_url,         # 혹시 다른 키를 참고해도 되게 중복 제공
    "filename": filename
  }), 200

# 상품 수정
@bp.put("/edit/<int:id>")
def edit_goods(id):
  data = request.get_json()

  category = data.get('category')
  classify = data.get('classify')
  price = int(data.get('price', 0))
  goods_name = data.get('goods_name')
  goods_desc = data.get('goods_desc')
  stock = int(data.get('stock', 0))
  image_path = data.get('image_path')
  is_active = bool(data.get('is_active', True))

  missing = []
  if not category: missing.append("카테고리")
  if not classify: missing.append("분류")
  if not goods_name: missing.append("상품명")
  if not goods_desc: missing.append("상품 설명")
  if not price: missing.append("가격")
  if not stock: missing.append("재고")

  if missing:
    return jsonify({
      "ok" : False,
      "message" : f"수정 필수 항목 누락 : {','.join(missing)} "
    }), 400
  
  goods = db.session.query(Goods).get(id)

  if not goods:
    return jsonify({'ok': False, 'message': '상품을 찾을 수 없습니다.'}), 404
  
  if goods.user_id != current_user.id:
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
def delete_goods(id):
  goods = db.session.query(Goods).get(id)

  if not goods:
    return jsonify({'ok': False, 'message': '상품을 찾을 수 없습니다.'}), 404
  
  if goods.user_id != current_user.id:
    return jsonify({'ok' : False, 'message' : '작성자만 수정 가능합니다'}), 403
  
  try:
    db.session.delete(goods)
    db.session.commit()
  except Exception:
    db.session.rollback()
    return jsonify({'ok' : False, 'message' : '상품 삭제 실패'}), 500
  
  return jsonify({'ok' : True, 'message' : '상품 삭제 완료'}), 200

# 품절 상품
@bp.get("/goods/soldout")
def get_soldout_goods():
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

# 상품 리스트
@bp.get('/goods')
def board_list():
  page = request.args.get('page', type=int, default=1)
  per_page = 10
  goods_q = Goods.query.order_by(Goods.create_at.desc())
  goods = goods_q.paginate(page=page , per_page=per_page)

  
  return jsonify({
    'ok' : True,
    'goods' : [goods.to_dict() for goods in goods.items],
    'total' : goods.total,
    'page' : goods.page,
    'pages' : goods.pages,
    "per_page": per_page
  }), 200
  

  