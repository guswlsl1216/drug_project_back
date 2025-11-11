from flask import Blueprint, request, jsonify
from app import db
from app.models.favorite import Favorite
from app.models.auto import get_class
from datetime import datetime


bp = Blueprint('favorite', __name__)


# 찜 목록
@bp.post('/<int:goodsId>')
def toggle_favorite(goodsId):
  user_id = 1

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
      new_favorite = Favorite(goods_id=goodsId, user_id=user_id, created_at=datetime.now())
      db.session.add(new_favorite)
      db.session.commit()
      return jsonify({'ok':True, 'message':'찜 목록에 등록되었습니다.', 'is_favorite':True}), 200
  
  except Exception as e:
    db.session.rollback()
    print(f"찜 기능 처리 오류:{e}")
    return jsonify({'ok':False, 'message':'서버 오류로 찜 상태를 변경할 수 없습니다.'}), 500
  

@bp.get('/check/<int:goodsId>')
def check_favorite_status(goodsId):
  user_id = 1 # 임시 사용자 ID

  try:
    favorite_item = Favorite.query.filter_by(goods_id=goodsId, user_id=user_id).first()

    if favorite_item:
      return jsonify({'ok':True, 'is_favorite':True}), 200
    else:
      return jsonify({'ok':True, 'is_favorite':False}), 200
  except Exception as e:
    print(f"오류 확인: {e}")
    return jsonify({'ok':False, 'message':'찜 상태 확인 중 서버 오류 발생'}), 500