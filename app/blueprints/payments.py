from flask import Blueprint, request, session, jsonify
import base64, requests
from app.config import Config
from ..extensions import db
from flask_jwt_extended import get_current_user, jwt_required
from ..models.order import Order
from ..models.orderitem import OrderItem
from ..models.payment import Payment
from ..models.goods import Goods
from ..models.cart import Cart

bp = Blueprint('payments', __name__)
original_string = Config.WIDGET_SECRET_KEY + ":"
encoded_key_string = base64.b64encode(original_string.encode("utf-8")).decode('utf-8')
encryptedSecretKey = f"Basic {encoded_key_string}"

# orderId와 amount를 세션에 임시 저장 / 주문 정보 DB 저장
@bp.post('/ready')
@jwt_required()
def save_payment_data():
  # 결제 요청 정보 세션 저장
  try:
    data = request.get_json()
    order_id = data.get('orderId')
    amount = data.get('amount')['value']

    if not order_id or not amount:
      return jsonify({'ok':False, 'message':'전송된 결제 요청 정보가 올바르지 않습니다.'}), 400
    
    session['pre_payment_order_id'] = order_id
    session['pre_payment_amount'] = amount
  except Exception as e:
    return jsonify({'ok':False, 'message':'결제 요청 정보 저장 중 에러가 발생했습니다.'}), 500
  
  # 주문 정보 DB 저장
  try:
    order_data = data.get('order')
    order_item_list = data.get('orderItem')

    if not order_item_list:
      return jsonify({"ok" : False, "message" : "주문 상품이 없습니다."}), 400
    
    # 재고 파악
    for item in order_item_list:
      goods = db.session.query(Goods).filter_by(id=item['goods_id']).first()
      if (not goods.is_active) or (goods.stock < item['count']):
        return jsonify({'ok':False, 'message':'품절된 상품이 있습니다.'}), 400
    
    user = get_current_user()
    db.session.add(user)
    user_id = user.id

    # 데이터 검증
    required_fields = ['receiver', 'phone', 'zipcode', 'address', 'address_detail']
    for field in required_fields:
      if not order_data or not order_data.get(field):
        return jsonify({'ok': False, 'message': f"필수 배송 정보가 누락되었습니다: {field}."}), 400

    try:
      items_total = sum(
        int(item.get("unit_price")) * int(item.get("count"))
        for item in order_item_list
      )
      total_count = sum(int(item.get("count")) for item in order_item_list)
      shipping_fee = int(order_data.get("shipping_fee", 0))
      used_points= int(order_data.get("used_points", 0))
    except (KeyError, TypeError, ValueError) as e:
      print(f"Order data processing failed: {e}")
      return jsonify({"ok": False, "message": "잘못된 주문 데이터입니다."}), 400

    final_amount = items_total +  shipping_fee - used_points
    if final_amount < 0:
      final_amount = 0

    client_final = int(order_data.get("final_amount", 0))
    if client_final != final_amount:
      return jsonify({"ok": False, "message": "결제 금액이 올바르지 않습니다."}), 400
    
    if used_points > 0:
      if not user or (user.point or 0) < used_points:
        return jsonify({"ok" : False, "message" : "보유 적립금이 부족합니다."}), 400
    
    saved_points = ( items_total - used_points ) * 0.01
    if saved_points < 0:
      saved_points = 0

    # 주문 테이블 저장
    order = Order(
      user_id=user_id,
      items_total=items_total,      # 상품 총합
      shipping_fee=shipping_fee,
      used_points=used_points,
      saved_points=saved_points,
      final_amount=final_amount,    # 최종 결제금액 (items_total + shipping - points)
      total_count=total_count,      # 총 수량
      status="PENDING",
      zipcode=order_data.get("zipcode"),
      address=order_data.get("address"),
      address_detail=order_data.get("address_detail"),
      address_extra=order_data.get("address_extra", ""),  
      receiver=order_data.get("receiver"),
      phone=order_data.get("phone"),
      delivery_message=order_data.get("delivery_message") or None, 
      order_code = order_id
    ) 

    db.session.add(order)
    db.session.flush()  # order.id 가져오려고 (commit 전에 PK 생성)

    # 주문항목 테이블 저장
    for item in order_item_list:
      order_item = OrderItem(
        orders_id=order.id,
        goods_id=item.get("goods_id"),
        unit_price=item.get("unit_price"),
        count=item.get("count"),
        subtotal=item.get("subtotal"),
        cart_id = item.get("cart_id")
      )
      db.session.add(order_item)

    # 배송지 저장 체크 시 user 테이블에 저장
    saveAddress = data.get('saveAddress')
    if saveAddress:
      user.address = order_data.get("address")
      user.detail=order_data.get("address_detail")
      user.zipcode=order_data.get("zipcode")

      if not user.tel:
        user.tel = order_data.get("phone")

    db.session.commit()
    return jsonify({'ok':True, 'message':'결제 요청 정보 및 주문 정보가 저장되었습니다.'}), 200
  except Exception as e:
    db.session.rollback()
    print(f"주문 정보 DB 저장 중 에러 발생 : {e}")
    return jsonify({'ok':False, 'message':'주문 정보 DB 저장 중 에러가 발생했습니다.'}), 500

# 결제 정보 검증 & 결제 승인
@bp.post('/approve')
@jwt_required()
def confirm_payment():
  try:
    data = request.get_json()
    order_id = data.get('orderId')
    amount = data.get('amount')
    payment_key = data.get('paymentKey')

    if not order_id or not amount:
      return jsonify({'ok':False, 'message':'전송된 결제 정보가 올바르지 않습니다.'}), 400

    user = get_current_user()
    db.session.add(user)

    order = db.session.query(Order).filter_by(order_code=order_id).first()
    if not order:
      return jsonify({'ok': False, 'message': 'DB에 해당 주문 정보가 없습니다.'}), 404
    
    order_items = db.session.query(OrderItem).filter_by(orders_id=order.id).all()
    serialized_items = [item.to_dict() for item in order_items]

    # 이미 승인된 건이면 건너뛰기
    if order.status in ("PAID"):
      return jsonify({
        'ok':True,
        'message':'이미 처리된 주문입니다.',
        'order_items': serialized_items,
        'final_amount': order.final_amount,
        'order_code': order.order_code
        }), 200

    if order_id != session.get('pre_payment_order_id') or amount != session.get('pre_payment_amount'):
      return jsonify({'ok':False, 'message':'잘못된 결제 정보입니다.'}), 400
    
    # 결제 승인
    toss_api_url = "https://api.tosspayments.com/v1/payments/confirm"
    headers = {
      "Authorization": encryptedSecretKey, 
      "Content-Type": "application/json"
    }
    body = {
      "orderId": order_id,
      "amount": amount,
      "paymentKey": payment_key
    }

    try:
      response = requests.post(toss_api_url, headers=headers, json=body)

      if response.status_code == 200:
        # 결제 주문 정보 db 저장
        toss_response = response.json()
        paymentKey = toss_response['paymentKey']

        # 간편결제만 한다고 가정
        # 간편결제 외 다른 결제수단 선택 시 type에는 method 값이 들어감
        method = toss_response['method']
        easy_pay_info = toss_response.get('easyPay')
        if easy_pay_info:
            payment_type = easy_pay_info.get('provider') 
        else:
            payment_type = method

        payment = Payment(
          orders_id = order.id,
          user_id = user.id,
          paymentKey = paymentKey,
          amount = toss_response['totalAmount'],
          type = payment_type,
          method = method,
          status = toss_response['status'],
          pg_tid = toss_response['lastTransactionKey'],
          receipt_url = toss_response['receipt']['url'],
          paid_at = toss_response['approvedAt']
        )

        order.status = "PAID"
        db.session.add(payment)

        # 결제 완료 시 goods 테이블 수정
        for item in order_items:
          goods = db.session.query(Goods).filter_by(id=item.goods_id).with_for_update().first()
          goods.sell_count += item.count
          updated_stock = goods.stock - item.count
          if updated_stock <= 0:
            goods.stock = 0
            goods.is_active = False
          else:
            goods.stock = updated_stock

        # 결제 완료 시 포인트 차감 및 적립
        user.point = user.point - order.used_points + order.saved_points
        if user.point < 0:
          user.point = 0

        # 결제 완료 시 cart 테이블 수정
        # 주문 항목에서 NULL이 아닌 고유한 cart_id 목록 추출
        cart_ids_to_delete = {item.cart_id for item in order_items if item.cart_id is not None}
        # 목록을 돌며 해당 cart_id 레코드 삭제
        for cart_id in cart_ids_to_delete:
          cart = db.session.query(Cart).filter_by(id=cart_id).with_for_update().first()
          if cart:
            db.session.delete(cart)

        try:
          db.session.commit()
          return jsonify({
              'ok':True,
              'message':'결제 승인이 완료되었습니다.',
              'order_items': serialized_items,
              'final_amount': order.final_amount,
              'order_code': order.order_code
            }), 200
        except Exception as e:
          db.session.rollback()
          # 결제 취소
          toss_api_url = f"https://api.tosspayments.com/v1/payments/{paymentKey}/cancel"
          headers = {
            "Authorization": encryptedSecretKey, 
            "Content-Type": "application/json"
          }
          body = {
            "cancelReason": "결제 처리 중 오류 발생",
          }

          requests.post(toss_api_url, headers=headers, json=body)

          try:
            order.status = "CANCELLED"
            db.session.commit()
            session.pop('pre_payment_order_id', None)
            session.pop('pre_payment_amount', None)
          except Exception as commit_e:
            print(f"결제 취소 처리 실패: {commit_e}")

          print(f'결제 정보 DB 저장 중 오류가 발생했습니다. : {e}')
          return jsonify({'ok':False, 'message': '결제 정보 DB 저장 중 오류가 발생했습니다.'}), 500
      else:
        return jsonify({'ok': False, 'message': '결제 승인 API 호출에 실패했습니다.', 'details': response.json()}), response.status_code
    except requests.exceptions.RequestException as e:
      return jsonify({'ok': False, 'message': f'API 통신 에러가 발생했습니다.: {str(e)}'}), 500
  except Exception as e:
    print(f'결제 승인 중 에러가 발생했습니다. : {e}')
    return jsonify({'ok':False, 'message':'결제 승인 중 에러가 발생했습니다.'}), 500