from flask import jsonify
from functools import wraps
from flask_jwt_extended import get_current_user

def requires_ownership(model, url_id_field='id', user_field='user_id'):
  """
  리소스 소유권을 확인하는 데코레이터.
  - model: 확인할 데이터베이스 모델 클래스 (예: Analyze_result)
  - url_id_field: URL에서 리소스 ID를 가져오는 인자의 이름 (기본값 : id)
  - user_field: 모델 인스턴스에서 소유자 ID를 가져오는 필드의 이름 (기본값 : user_id)
  """
  def decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      resource_id = kwargs.get(url_id_field)

      resource = model.query.get(resource_id)
      if not resource:
        return jsonify({'ok': False, 'message': '리소스를 찾을 수 없습니다.'})
      
      user = get_current_user()
      current_user_id = user.id
      resource_owner_id = getattr(resource, user_field, None)

      if current_user_id != resource_owner_id:
        return jsonify({'ok':False, 'message':'접근 권한이 없습니다.'}), 403

      return f(*args, **kwargs)
    return decorated_function
  return decorator