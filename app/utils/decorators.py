from functools import wraps
from flask import jsonify
from ..models.user import User
from ..extensions import db
from ..utils.auth_user import get_current_user

def admin_required(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    user_id = get_current_user()
    user = db.session.query(User).get(user_id)

    if  not user or user.role != "admin":
      return jsonify({"ok" : False, "message" : "관리자만 사용할 수 있습니다."}), 403
    
    return f(*args, **kwargs)
  
  return decorated