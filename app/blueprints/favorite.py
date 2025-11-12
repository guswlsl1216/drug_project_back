from flask import Blueprint, request, jsonify
from app import db
from app.models.favorite import Favorite
from app.models.goods import Goods
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity


bp = Blueprint('favorite', __name__)


# 찜 목록
@bp.post('/<int:goodsId>')
@jwt_required()
def toggle_favorite(goodsId):
  user_id = get_jwt_identity() # 현재 로그인된 사용자 ID 가져오기

  # 찜 상태 조회
  favorite_item = Favorite.query.filter_by(goods_id=goodsId, user_id=user_id).first()

  try:
    if favorite_item:
      # 찜 삭제
      db.session.delete(favorite_item)
      db.session.commit()
      return jsonify({'ok':True, 'message':'찜 목록에서 삭제되었습니다.', 'is_favorite':False}), 200
    else:
      # 찜 등록
      new_favorite = Favorite(goods_id=goodsId, user_id=user_id, create_at=datetime.now())
      db.session.add(new_favorite)
      db.session.commit()
      return jsonify({'ok':True, 'message':'찜 목록에 등록되었습니다.', 'is_favorite':True}), 200
  
  except Exception as e:
    db.session.rollback()
    print(f"찜 기능 처리 오류:{e}")
    return jsonify({'ok':False, 'message':'서버 오류로 찜 상태를 변경할 수 없습니다.'}), 500
  

@bp.get('/list')
@jwt_required()
def get_favorite_list():
  user_id = get_jwt_identity()

  try:
    favorites_query = Favorite.query.filter_by(user_id=user_id).all()

    favorite_list = []

    for item in favorites_query:
      goods = Goods.query.filter_by(id=item.goods_id).first()

      if goods:
        favorite_list.append({
          'id':goods.id,
          'goods_name':goods.goods_name,
          'price':goods.price,
          'image_path':goods.image_path,
          'create_at':item.create_at.isoformat() # 찜한 시간
        })
    
    return jsonify({'ok':True, 'favorites':favorite_list}), 200
  
  except Exception as e:
    print(f"찜 목록 조회 오류: {e}")
    return jsonify({'ok':False, 'message':'찜 목록을 불러오는 데 실패했습니다.'}), 500


# 찜 상태 확인
@bp.get('/check/<int:goodsId>')
@jwt_required(optional=True)
def check_favorite_status(goodsId):
  user_id = get_jwt_identity()

  if user_id is None:
    return jsonify({'ok':True, 'is_favorite':False}), 200
  
  try:
    favorite_item = Favorite.query.filter_by(goods_id=goodsId, user_id=user_id).first()

    if favorite_item:
      return jsonify({'ok':True, 'is_favorite':True}), 200
    else:
      return jsonify({'ok':True, 'is_favorite':False}), 200
  except Exception as e:
    print(f"오류 확인: {e}")
    return jsonify({'ok':False, 'message':'찜 상태 확인 중 서버 오류 발생'}), 500