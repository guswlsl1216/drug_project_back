# JWT 보호

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..utils.response import make_response

bp = Blueprint("protected",__name__)

@bp.get("/protected")
@jwt_required() # jwt 유효성 검증
def protected():
  current_user_id = get_jwt_identity() # jwt payload 안에 있는 user_id 가져오기
  return make_response(
    ok=True,
    data={"logged_in_as":current_user_id}
  )