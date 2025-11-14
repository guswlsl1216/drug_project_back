from flask import Blueprint, request, session, jsonify
import base64, requests
from app.config import Config

bp = Blueprint('payments', __name__)
original_string = Config.WIDGET_SECRET_KEY + ":"
encoded_key_string = base64.b64encode(original_string.encode("utf-8")).decode('utf-8')
encryptedSecretKey = f"Basic {encoded_key_string}"

# orderId와 amount를 세션에 임시 저장
@bp.post('/ready')
def save_payment_data():
  try:
    data = request.get_json()
    order_id = data.get('orderId')
    amount = data.get('amount')['value']

    if not order_id or not amount:
      return jsonify({'ok':False, 'message':'전송된 결제 요청 정보가 올바르지 않습니다.'}), 400
    
    session['pre_payment_order_id'] = order_id
    session['pre_payment_amount'] = amount

    return jsonify({'ok':True, 'message':'결제 요청 정보가 저장되었습니다.'}), 200
  except Exception as e:
    return jsonify({'ok':False, 'message':'결제 요청 정보 저장 중 에러가 발생했습니다.'}), 500

# 결제 정보 검증 & 결제 승인
@bp.post('/approve')
def confirm_payment():
  try:
    data = request.get_json()
    order_id = data.get('orderId')
    amount = data.get('amount')
    payment_key = data.get('paymentKey')

    if not order_id or not amount:
      return jsonify({'ok':False, 'message':'전송된 결제 정보가 올바르지 않습니다.'}), 400

    # 결제 정보 검증
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
        session.pop('pre_payment_order_id', None)
        session.pop('pre_payment_amount', None)
        # 결제 주문 정보 db 저장
        # 결제 테이블은 payments객체 (지금 여기서는 response.json())에서 뽑아서 넣을 수 있음
        
        return jsonify({'ok':True, 'toss_response': response.json()}), 200
      else:
        return jsonify({'ok': False, 'message': '결제 승인 API 호출 실패', 'details': response.json()}), response.status_code
    except requests.exceptions.RequestException as e:
      return jsonify({'ok': False, 'message': f'API 통신 에러 발생: {str(e)}'}), 500
  except Exception as e:
    return jsonify({'ok':False, 'message':'결제 승인 중 에러가 발생했습니다.'}), 500