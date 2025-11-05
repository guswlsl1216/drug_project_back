from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime

from ..extensions import db
from ..models.analyze_result import Analyze_result

bp = Blueprint('analyze_result', __name__)

STATUS = {0:'정상', 1:'주의', 2:'위험'}

@bp.get('/test')
def test():
  return 'test'


# 분석 결과 내역
@bp.get('/history')
def get_history():
  page = request.args.get('page', type=int, default=1)

  history = Analyze_result.query\
              .filter(Analyze_result.user_id == current_user.id)\
              .order_by(Analyze_result.analysis_date.desc())
  
  history = history.paginate(page=page, per_page=10)

  return jsonify({
    'ok':True,
    'history':[h.to_dict() for h in history]
  })