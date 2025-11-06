from flask import Blueprint, jsonify, request
from app import db
from flask_login import current_user, login_required
from ..models.auto import get_class
from sqlalchemy import or_
from sqlalchemy import func

bp = Blueprint('aiAnalyze', __name__)
  
MP = get_class("meds_products")
SP = get_class("supps_products")

@bp.route('/medicine/search', methods=['GET'])
@bp.route('/supplements/search', methods=['GET'])
def search_meds():
  
  search_name = request.args.get('q', '').strip()
  search_type = request.args.get('type')

  if not search_type or search_type not in ['supps', 'meds']:
    return jsonify({ 'error' : 'type은 반드시 meds 또는 supps 여야 합니다. '}), 400
  
  model = SP if search_type == 'supps' else MP

  normalized_search_name = search_name.replace(' ', '').lower()
  search_keyword = f"%{normalized_search_name}%"

  column_name = model.PRDLST_NM if search_type == 'supps' else model.ITEM_NAME   

  results = (
    db.session.query(model.id, column_name)
    .filter(
      func.lower(func.replace(column_name, ' ', '')).like(search_keyword)
    ).all()
  )

  data = [{ "id" : r[0], "name" : r[1]} for r in results]
  return jsonify({
        'success': True,
        # 프론트엔드가 'medicines' 키를 예상하므로 여기에 데이터를 담습니다.
        'medicines': data 
    })

