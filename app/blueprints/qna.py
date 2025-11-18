from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..models.qna import QnA
from ..models.user import User
from ..extensions import db
import logging

bp = Blueprint('qna', __name__)

# QnA 등록
@bp.route('/<int:goods_id>', methods=['POST'])
@jwt_required(optional=True)
def create_qna(goods_id):
  user_id = get_jwt_identity()

  if request.is_json:
    data = request.get_json()
  else:
    data = request.form

  title = data.get("question_title")
  content = data.get("question_content")
  is_private = data.get("is_private", False)

  if isinstance(is_private, str):
    is_private = is_private.lower() == "true"
  elif isinstance(is_private, bool):
    pass
  else:
    is_private = False

  if not title or not content:
    return jsonify({
      'ok':False,
      'message':'제목과 내용을 모두 입력해주세요'
    }), 400

  
  try:
    new_qna = QnA(
      user_id=user_id,
      goods_id=goods_id,
      question_title=title,
      question_content=content,
      is_private=is_private,
      created_at=datetime.now(),
      status="pending"
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
      q_content = "비밀글입니다."
    else:
      q_content = qna.question_content

    output.append({
      'id':qna.id,
      'user_nickname':qna.user.nickname if qna.user else '탈퇴 회원',
      'title':q_content,
      'question': qna.question_content if not qna.is_private else None,
      'answer':qna.answer_content,
      'status':qna.status,
      'is_private':qna.is_private,
      'created_at':qna.created_at.strftime('%Y-%m-%d %H:%M'),
      'answered_at':(
        qna.answered_at.strftime('%Y-%m-%d %H:%M')
        if qna.answered_at else None
      )
    })
  
  return jsonify({'ok':True, 'qna_list':output})