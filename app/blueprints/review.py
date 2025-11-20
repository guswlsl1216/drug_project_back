from datetime import datetime
import os
import pickle
from flask import Blueprint, app, current_app, jsonify, request, g
from flask_jwt_extended import get_current_user, get_jwt_identity, jwt_required, verify_jwt_in_request
from flask_login import current_user, login_required
from app import db
from ..models.user import User
from ..models.review import Review
from ..models.goods import Goods
from werkzeug.utils import secure_filename
from ..extensions import tokenizer, model
import torch

bp = Blueprint('review', __name__)

#이미지파일 형식 멀쩡한가
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#받은 이미지 서버경로로 바꾸기
def change_path(image):
  filename = secure_filename(image.filename)
  save_path = os.path.join(current_app.root_path,'static','review', filename)
  image.save(save_path)
  return f"/static/review/{image.filename}"

def text_filter(text):
    inputs = tokenizer(
        text,
        return_tensors='pt',
        truncation=True,
        max_length=512,
        padding=True
    )
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=1)
        prediction = torch.argmax(logits, dim=1).item()
        confidence = probabilities[0][prediction].item()
    
    # 문자열로 반환
    label = '악플' if prediction == 1 else '정상'
    
    return label, prediction

@bp.before_request
def before_api_request():
    
    if request.method == 'OPTIONS':
      return
    
    # 특정 엔드포인트는 인증 생략
    skip_list = [
        'review.getReview',
        'review.goodsReviewInfo'# 블루프린트명.엔드포인트명
    ]
    if request.endpoint in skip_list:
        return
    
    # JWT 검증을 직접 수행
    try:
        verify_jwt_in_request()
        # get_jwt_identity()로 user_id 가져오기
        current_user_id = get_jwt_identity() 
        
        # 직접 데이터베이스에서 사용자 조회
        g.user = User.query.get(current_user_id)
    except Exception as e:
        print('-----------', e)
        return jsonify({'ok': False, 'message': '인증 실패ㅋㅋ'}), 401

#부적절한 내용 감지 시 추가하지 않음
@bp.post('/addReview/<goods_id>')
def addReview(goods_id): 
  content=request.form.get('content')
  user_id=g.user.id
  stars=request.form.get('stars')
  
  review_check, review_prediction = text_filter(content)
  print('-----------------------')
  print('review_prediction:',review_prediction)
  print('-----------------------')
  if review_check=='악플':
    return jsonify({'ok':False, 'message':'부적절한 단어가 포함되어있습니다'})
  
  image_path = None
  image = request.files.get('image')
  if image:
    if allowed_file(image.filename):
      image_path = change_path(image)
    else:
      return jsonify({'ok':False, 'message':'파일형식이 올바르지 않습니다'})
  
  review = Review(content=content, stars=stars, goods_id=goods_id, user_id=user_id, review_image=image_path)
  db.session.add(review)
  db.session.commit()

  return jsonify({'ok':True, 'message':'댓글등록완료'}),200

@bp.get('/getReview/<goods_id>')
def getReview(goods_id):
  goods = db.session.query(Goods).get(goods_id)
  reviews = goods.reviews
  review_list = []
  for review in reviews:
    review_list.append(review.to_dict())
  return jsonify({'ok':True, 'reviews':review_list}),200

@bp.delete('/deleteReview/<reviewId>')
def deleteRoutine(reviewId):
  review=db.session.query(Review).get(reviewId)
  if review.user_id == g.user.id:
    db.session.delete(review)
    db.session.commit()
    return jsonify({'ok':True, 'message':'댓글삭제 완료'}),200
  return jsonify({'ok':False, 'message':'유저id가 일치하지 않습니다'})

@bp.put('/updateReview/<reviewId>')
def updateReview(reviewId):
  current_review=db.session.query(Review).get(reviewId)
  if current_review.user_id == g.user.id:
    content=request.form.get('content')
    stars=request.form.get('stars')
    
    review_check, review_prediction = text_filter(content)
    print('-----------------------')
    print('review_prediction:',review_prediction)
    print('-----------------------')
    if review_check=='악플':
      return jsonify({'ok':False, 'message':'부적절한 단어가 포함되어있습니다'})
    
    image=request.files.get('image')
    print(image)
    image_path = current_review.review_image
    if image:
      if allowed_file(image.filename):
        image_path = change_path(image)
      else:
        return jsonify({'ok':False, 'message':'파일형식이 올바르지 않습니다'})

    current_review.content=content
    current_review.stars=stars
    current_review.review_image=image_path

    db.session.add(current_review)
    db.session.commit()
    return jsonify({'ok':True, 'message':'댓글수정 완료'}),200
  return jsonify({'ok':False, 'message':'유저id가 일치하지 않습니다'})

@bp.get('/goodsReviewInfo/<goods_id>')
def goodsReviewInfo(goods_id):
  goods = db.session.query(Goods).get(goods_id)
  reviews = goods.reviews
  total = 0
  if not reviews:
    info={'length':0, 'star_avg':0}
    return jsonify({'ok':True, 'info':info})
  for review in reviews:
    total+=review.stars
  star_avg = float(round(total / len(reviews), 2))
  info={'length':len(reviews), 'star_avg':star_avg}
  return jsonify({'ok':True, 'info':info})