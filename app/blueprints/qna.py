from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..models.qna import QnA
from ..models.user import User
from ..extensions import db

bp = Blueprint('qna', __name__)

# QnA 등록
@bp.route('/<int:goods_id>', methods=['POST'])
@jwt_required()
def create_qna(goods_id):
  user_id = get_jwt_identity()
  data = request.get_json()

  if not data.get('question_title') or not data.get('question_content'):
    return jsonify({'ok': False, 'message':'제목과 내용은 필수입니다.'}), 400
  
  try:
    new_qna = QnA(
      user_id=user_id,
      goods_id=goods_id,
      question_title=data['question_title'],
      question_content=data['question_content'],
      is_private=data.get('is_private', False),
      create_at=datetime.now()
    )
    db.session.add(new_qna)
    db.session.commit()
    return jsonify({'ok':True, 'message':'질문이 성공적으로 등록되었습니다.'}), 200
  except Exception as e:
    db.session.rollback()
    return jsonify({'ok':False, 'message':f'질문 등록 실패: {str(e)}'}), 500
  

# 목록 조회
@bp.route('/<int:goods_id>', methods=['GET'])
def get_qna_list(goods_id):
  qna_list = QnA.query.filter_by(goods_id=goods_id).order_by(QnA.created_at.desc()).all()

  output = []
  for qna in qna_list:
    # 비밀글 처리 (로그인한 사용자나 관리자만 볼 수 있게)
    if qna.is_private:
      questioner = qna.user.nickname if qna.user else '알 수 없음'
      if not qna.answer_content:
        q_content = "비밀글입니다."
      else:
        q_content = "비밀글입니다." # 답변이 있어도 내용 감추기
    else:
      q_content = qna.question_content

    output.append({
      'id':qna.id,
      'user_nickname':qna.user.nickname if qna.user else '탈퇴 회원',
      'title':q_content,
      'answer':qna.answer_content,
      'status':qna.status,
      'is_private':qna.is_private,
      'created_at':qna.created_at.strftime('%Y-%m-%d %H:%M')
    })
  
  return jsonify({'ok':True, 'qna_list':output})