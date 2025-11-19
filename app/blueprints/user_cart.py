from ..extensions import db
from sqlalchemy.orm import joinedload
from ..models.cart import Cart
from ..models.goods import Goods
from ..utils.auth_user import get_current_user
from ..utils.requires_ownership import requires_ownership
from flask import Blueprint, Flask, request, render_template, redirect, url_for, g, jsonify
from flask_jwt_extended import jwt_required, current_user

bp = Blueprint('cart',__name__)

# user 장바구니 목록을 불러 옴
# 수량,합계 추가예정
@bp.get('/')
@jwt_required()
def get_cart():
  user = current_user

  # 장바구니 상품들
  cart_items = (
    db.session.query(
      Cart.id.label("cart_id"),
      Cart.count,
      Cart.user_id,
      Goods.id.label("goods_id"),
      Goods.stock,
      Goods.goods_name,
      Goods.image_path,
      Goods.price
    )
    .join(Goods, Cart.goods_id == Goods.id)
    .filter(Cart.user_id == user.id)
    .all()
  )
  print("="*20,cart_items)

  result = []
  for c in cart_items:
    result.append({
      'cart_id':c.cart_id,
      'count':c.count,
      'goods_id':c.goods_id,
      'goods_name':c.goods_name,
      'stock':c.stock,
      'user_id':c.user_id,
      'image_path':c.image_path,
      'price':c.price
    })
  

  return jsonify(result)

# 상품 수량 변경(증가, 감소) -> 버튼에만 사용
@bp.put('/<int:cart_id>')
@jwt_required()
def update_goods(cart_id):

  cart_item = Cart.query.filter_by(id=cart_id).first()
  data = request.get_json() 
  action = data.get('action')
  
  goods_item = cart_item.goods # Cart 모델의 relationship을 총해 Goods 객체 접근
  stock = goods_item.stock # 해당 상품의 재고를 가져 옴
  
  print("="*20)
  print(stock)
  print(cart_item.count)
  print(action)

  if cart_item and action == 'plus': # 재고 수량 초과 시 더 못 넣게 구현을 해야하는데 그건 프론트에서 해야할지?
    if int(stock) > int(cart_item.count):

      cart_item.count += 1
      db.session.commit()
    else:
      return jsonify({'error':'재고 수량을 초과하였습니다.'}),400
      
  elif cart_item and action == 'minus': # 1개 이하로 안 내려가게 수정
    if cart_item.count > 1:
      cart_item.count -= 1
      db.session.commit()
    else:
      return jsonify({'error':'최소 수량은 1개입니다.'}),400
    
  result = {
    'id':cart_item.id,
    'count':cart_item.count,
  }
  return jsonify(result)

# 장바구니 상품 수량 변경 (현재 추가만 가능->상품 상세 페이지에서 추가용)
# 추후 수량 여러개 count 만큼 추가 해야된다면 수정 필요, 현재 1개만 추가 됨
@bp.post('/<int:goods_id>')
@jwt_required()
def post_goods(goods_id):
  user = current_user
  message = ""
  cart = Cart.query.filter_by(user_id=user.id, goods_id=goods_id).first()
  data = request.get_json()
  new_count = data['count'] # 상품 담을 수량
  
  if cart is None : # 담긴게 없어서 새로 추가 할 때 setQuantity(수량)을 받아서 넣어줘야 함
    cart = Cart(user_id=user.id, goods_id=goods_id, count=new_count)
    db.session.add(cart)
    db.session.commit()

    # 장바구니에 있는 count와 setQuantity의 수량이 stock(재고)를 넘으면 안 담기게 하거나 맞는 개수만 들어가게

  else : # 담긴 게 있다면 위의 주석대로 ㄱ
    stock = cart.goods.stock # 재고
    add_count = cart.count+new_count # 장바구니개수+상품 담을 수량(총 담을 개수)
    
    if add_count > stock :
      cart.count = min(add_count, stock) # 재고 제한
      message = f"재고가 부족하여 {stock}개 까지만 담을 수 있습니다."
    else:
      cart.count = add_count

  db.session.commit()

  result = {
    'id':cart.id,
    'count':cart.count,
    'goods_id':cart.goods_id,
    'message':message
  }

  return jsonify(result)

# cart id로 삭제 -> 다중 선택 삭제로 할 수 있도록 list 필요
@bp.delete('/<int:cart_id>')
@jwt_required()
def delete_goods(cart_id):

  goods = Cart.query.filter_by(id=cart_id).first()

  if goods is None:
    return jsonify({'error':'해당 목록이 존재하지 않습니다.'})
  
  result = [goods]
  for item in result:
    db.session.delete(item)

  db.session.commit()

  return jsonify({'id':cart_id})




  