from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
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
@jwt_required(optional=True)
def get_qna_list(goods_id):
  current_user_id = get_jwt_identity()
  claims = get_jwt()
  current_user_role = claims.get('role')

  qna_list = QnA.query.filter_by(goods_id=goods_id).order_by(QnA.created_at.desc()).all()

  output = []

  for qna in qna_list:
    can_view = False

    if current_user_role and current_user_role == 'admin': # JWT의 role이 'admin'이면 무조건 허용(DB 조회 불필요)
      can_view = True
    
    elif str(current_user_id) == str(qna.user_id): # 질문 작성자
      can_view = True

    elif qna.admin_id and str(current_user_id) == str(qna.admin_id):  # QnA의 관리자 (답변을 단 관리자)
      can_view = True
    
    elif qna.goods and qna.goods.user and qna.goods.user.role == "admin": # 상품등록자가 admin인 경우
      can_view = True
      
    # 비밀글 처리 (로그인한 사용자나 관리자만 볼 수 있게)
    if qna.is_private and not can_view:
      q_content = "비밀글입니다."
      q_answer = "비밀글입니다."
    else:
      q_content = qna.question_content
      q_answer = qna.answer_content

    output.append({
      'id':qna.id,
      'user_nickname':qna.user.nickname if qna.user else '탈퇴 회원',
      'title':qna.question_title,
      'content':q_content,
      'answer':q_answer,
      'status':qna.status,
      'is_private':qna.is_private,
      'created_at':qna.created_at,
      'is_owner':str(current_user_id) == str(qna.user_id),
      'answered_at':(
        qna.answered_at
        if qna.answered_at else None
      )
    })
  
  return jsonify({'ok':True, 'qna_list':output})


@bp.route('/<int:qna_id>/answer', methods=['POST'])
@jwt_required(optional=True)
def create_answer(qna_id):
  current_user_id = get_jwt_identity()
  claims = get_jwt()
  current_user_role = claims.get('role')

  # 관리자 권한 확인
  if current_user_role != 'admin':
    return jsonify({'ok':False, 'message':'답변을 등록할 권한이 없습니다. (관리자만 가능)'}), 403
  
  # 데이터 유효성 검사 및 QnA 조회
  data = request.get_json() if request.is_json else request.form
  answer_content = data.get("answer_content")

  if not answer_content:
    return jsonify({'ok':False, 'message':'답변 내용을 입력해주세요.'}), 400
  
  qna = QnA.query.get(qna_id)
  if not qna:
    return jsonify({'ok':False, 'message':'해당 QnA를 찾을 수 없습니다.'}), 404
  
  try:
    try:
      admin_id_int = int(current_user_id)
    except (TypeError, ValueError):
      return jsonify({'ok':False, 'message':'사용자 ID 형식이 잘못되었습니다.'}), 400

    qna.admin_id = admin_id_int  # 답변을 단 관리자의 ID 저장
    qna.answer_content = answer_content
    qna.answered_at = datetime.now()
    qna.status = "answered"

    db.session.commit()

    return jsonify({'ok':True, 'message':'답변이 성공적으로 등록되었습니다.'}), 200
  except Exception as e:
    db.session.rollback()
    logging.error(f"답변 등록 오류: {str(e)}")
    return jsonify({'ok':False, 'message':f"답변 등록 실패: {str(e)}"}), 500
  

# 질문 수정(답변 달리기 전에만 가능)
@bp.route('/<int:qna_id>', methods=['PUT'])
@jwt_required()
def update_qna(qna_id):
  current_user_id = get_jwt_identity()
  
  qna = QnA.query.get(qna_id)
  if not qna:
    return jsonify({'ok':False,'message':'해당 QnA를 찾을 수 없습니다.'}), 404
  
  # 권한 확인: 작성자 또는 관리자만 수정가능
  if str(current_user_id) != str(qna.user_id):
    return jsonify({'ok':False, 'message':'수정 권한이 없습니다.'}), 403
  
  if qna.status == 'answered':
    return jsonify({'ok':False, 'message':'답변이 완료된 질문은 수정할 수 없습니다. 관리자에게 문의하세요'}), 400

  data = request.get_json() if request.is_json else request.form

  title = data.get('question_title', qna.question_title)
  content = data.get('question_content', qna.question_content)
  is_private_input = data.get('is_private')

  # is_private 처리 로직
  if isinstance(is_private_input, str):
    is_private = is_private_input.lower() == 'true'
  elif isinstance(is_private_input, bool):
    is_private = is_private_input
  else:
    is_private = qna.is_private # 입력이 없으면 기존 값 유지

  if not title or not content:
    return jsonify({'ok':False, 'message':'제목과 내용을 모두 입력해주세요'}), 400
  
  try:
    qna.question_title = title
    qna.question_content = content
    qna.is_private = is_private

    # 관리자가 답변을 달기 전이라면 수정가능
    # 답변 완료 상태는 400 에러

    db.session.commit()
    return jsonify({'ok':True,'message':'질문이 성공적으로 수정되었습니다.'}), 200
  except Exception as e:
    db.session.rollback()
    return jsonify({'ok':False, 'message':f'질문 수정 실패: {str(e)}'}), 500
  

@bp.route('/<int:qna_id>', methods=['DELETE'])
@jwt_required()
def delete_qna(qna_id):
  current_user_id = get_jwt_identity()
  claims = get_jwt()
  current_user_role = claims.get('role')

  qna = QnA.query.get(qna_id)
  if not qna:
    return jsonify({'ok':False, 'message':'해당 QnA를 찾을 수 없습니다.'}), 404
  
  # 권한 확인: 작성자 또는 관리자만 삭제 가능
  if str(current_user_id) != str(qna.user_id) and current_user_role != 'admin':
    return jsonify({'ok':False, 'message':'삭제 권한이 없습니다.'}), 403
  
  try:
    db.session.delete(qna)
    db.session.commit()
    return jsonify({'ok':True, 'message':'질문이 성공적으로 삭제되었습니다.'}), 200
  except Exception as e:
    db.session.rollback()
    return jsonify({'ok':False, 'message':f'질문 삭제 실패: {str(e)}'}), 500
  


# 관리자 답변 수정
@bp.route('/<int:qna_id>/answer', methods=['PUT'])
@jwt_required()
def update_answer(qna_id):
  current_user_id = get_jwt_identity()
  claims = get_jwt()
  role = claims.get('role')

  if role != 'admin':
    return jsonify({'ok':False, 'message':'관리자만 답변을 수정할 수 있습니다.'}), 403
  
  qna = QnA.query.get(qna_id)
  if not qna:
    return jsonify({'ok':False, 'message':'해당 QnA를 찾을 수 없습니다.'}), 404
  
  if str(qna.admin_id) != str(current_user_id):
    return jsonify({'ok':False, 'message':'본인이 작성한 답변만 수정할 수 있습니다.'}), 403
  
  data = request.get_json() if request.is_json else request.form
  answer_content = data.get('answer_content')

  if not answer_content:
    return jsonify({'ok':False, 'message':'답변 내용을 입력해주세요'}), 400
  
  try:
    qna.answer_content = answer_content
    qna.answered_at = datetime.now()
    db.session.commit()
    return jsonify({'ok':True, 'message':'답변이 성공적으로 수정되었습니다.'}), 200
  except Exception as e:
    db.session.rollback()
    return jsonify({'ok':False, 'message':f'답변 수정 실패: {str(e)}'}), 500