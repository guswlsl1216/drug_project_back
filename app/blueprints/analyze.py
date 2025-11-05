from flask import Blueprint, request, jsonify
from app.models.user_meds import UserMeds
from utils.db_helpers import get_db_connection
from utils.response import response_success, response_fail

bp = Blueprint('medicine', __name__, url_prefix='/medicine')

@bp.route('/search', methods=['GET'])
def search_medicines():
    """
    의약품 검색 API
    query params:
        - keyword: 검색할 의약품 이름
    returns:
        - medicines: [{ id: str, name: str, detail: str }]
    """
    try:
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({
                'success': True,
                'medicines': []
            })

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # meds_products 테이블에서 ITEM_NAME으로 검색
        query = """
            SELECT 
                ITEM_SEQ as id,
                ITEM_NAME as name,
                ENTP_NAME as detail
            FROM meds_products 
            WHERE ITEM_NAME LIKE %s
            LIMIT 10
        """
        search_term = f"%{keyword}%"
        cursor.execute(query, (search_term,))
        medicines = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return response_success(data={
            'medicines': medicines
        })
        
    except Exception as e:
        return response_fail(str(e))

# 추가 기능을 위한 라우트들을 여기에 추가할 수 있습니다.