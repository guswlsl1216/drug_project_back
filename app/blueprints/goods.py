from flask import Blueprint, request, jsonify
from app import db
from app.models.goods import Goods
from app.models.favorite import Favorite
from app.models.supps_products import SuppsProducts
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from urllib.parse import unquote


bp = Blueprint('goods', __name__)


FILTER_MAP = {
  'category': Goods.category, # 기능성
  'classify': Goods.classify  # 성분별
}

SORT_MAP = {
  'newest': Goods.create_at,  # 신상품순
  'sales':Goods.sell_count,   # 판매순
  'price':Goods.price,        # 가격순
  'popularity':Goods.sell_count # 인기순(임시)
}

# 상품 목록 조회 및 정렬/필터링
@bp.get('/')
def get_goods_list():
  try:
    user_id = None

    try: # 토큰이 유효하면 사용자 ID를 가져옴(로그인 상태)
      verify_jwt_in_request(optional=True)
      user_id = get_jwt_identity()
    except Exception:
      user_id = None

    raw_category_key = request.args.get('category_key')
    raw_category_value = request.args.get('category_value')
    raw_goods_name = request.args.get('goods_name')

    category_key = unquote(raw_category_key) if raw_category_key else None
    category_value = unquote(raw_category_value) if raw_category_value else None
    sort_by = request.args.get('sort_by', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Goods.query

    if raw_goods_name:
      goods_name_search = unquote(raw_goods_name)
      query = query.filter(Goods.goods_name.ilike(f"%{goods_name_search}%"))

    # 카테고리 필터링 로직
    if category_value and category_value != 'All':

      if category_key in FILTER_MAP:
        filter_field = FILTER_MAP.get(category_key)
        query = query.filter(filter_field == category_value)

    # 정렬 로직
    sort_field = SORT_MAP.get(sort_by)

    if sort_field is not None:
      # 낮은가격순은 오름차순(asc)
      if sort_by == 'price':
        query = query.order_by(sort_field.asc())
      # 신상품순, 판매순 등은 내림차순(desc)
      else:
        query = query.order_by(sort_field.desc())

    # 페이징 적용 및 데이터 조회
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    goods_list = pagination.items

    # JSON 응답 데이터 포맷팅
    formatted_goods = []
    for item in goods_list:
      goods_dict = item.to_dict()

      goods_dict['is_favorite'] = False

      if user_id is not None: # 로그인 했을 때만 실행되는 찜 상태 확인
        favorite_item = Favorite.query.filter_by(goods_id=item.id, user_id=user_id).first()
        if favorite_item:
          goods_dict['is_favorite'] = True

      formatted_goods.append(goods_dict)

    return jsonify({
      'ok':True,
      'goods':formatted_goods,
      'total_count':pagination.total,
      'total_pages':pagination.pages,
      'current_page':pagination.page
    }), 200
    
  except Exception as e:
    db.session.rollback()
    print(f"상품 목록 조회 오류: {e}")
    return jsonify({'ok':False, 'message':'서버 오류로 상품 목록을 불러올 수 없습니다.'}), 500
  

# 상품 상세 정보 조회
@bp.get('/<int:goodsId>')
def get_goods_detail(goodsId):
  try:
    user_id = None

    try: # 토큰이 유효하면 사용자 ID를 가져옴(로그인 상태)
      verify_jwt_in_request(optional=True)
      user_id = get_jwt_identity()
    except Exception:
      user_id = None

    # 상품ID로 조회 및 판매 활성화된 상품만 필터링
    product = Goods.query.filter_by(id=goodsId).first()

    if not product:
      return jsonify({'ok':False, 'message':'상품을 찾을 수 없습니다.'}), 404
    
    response_data = product.to_dict()

    response_data['is_favorite'] = False
    if user_id is not None:
      try:
        user_id = int(user_id)
      except:
        user_id = None
      
      if user_id is not None:
        favorite_item = Favorite.query.filter_by(goods_id=goodsId, user_id=user_id).first()
        if favorite_item:
          response_data['is_favorite'] = True

    return jsonify({'ok':True, 'product':response_data}), 200
  
  except Exception as e:
    print(f"상품 상세 조회 오류: {e}")
    return jsonify({'ok':False, 'message':'서버 오류로 상품 상세 정보를 불러올 수 없습니다.'}), 500
  
  #  상호작용 분석을 위한 영양제 상세 정보 조회 (프론트엔드 요청 경로 처리)
@bp.get('/aiAnalyze/supplements/detail/<int:goodsId>')
def get_supplement_detail_for_analysis(goodsId):
    try:
        # 1. Goods 테이블에서 상품 ID (예: 130)를 사용하여 레코드를 찾고, 
        #    연결된 supps_id (예: 136075)를 가져옵니다.
        goods_item = Goods.query.filter_by(id=goodsId, is_active=True).first()
        
        if not goods_item or not goods_item.supps_id:
            # 상품이 없거나 supps_id가 없는 경우
            return jsonify({'ok': False, 'message': f'상품 ID {goodsId}에 연결된 영양제 정보(supps_id)가 없습니다.'}), 404
            
        suppsId_to_lookup = goods_item.supps_id # 실제 조회할 ID: 136075
        
        # 2. supps_id (136075)를 사용하여 SuppsProducts 테이블에서 상세 정보를 조회합니다.
        supplement = SuppsProducts.query.filter_by(id=suppsId_to_lookup).first()

        if not supplement:
            # supps_products 테이블에 해당 ID의 레코드가 없는 경우
            return jsonify({'ok': False, 'message': f'supps ID {suppsId_to_lookup}에 해당하는 분석 정보를 찾을 수 없습니다.'}), 404

        # 3. 클라이언트가 요구하는 형식으로 데이터 반환 (원료명 포함)
        response_data = {
            'id': supplement.id,
            'name': supplement.PRDLST_NM,      
            'korName': supplement.BSSH_NM, 
            'ingredients': supplement.RAWMTRL_NM, # supps_products에서 원료명 추출
        }

        return jsonify(response_data), 200

    except Exception as e:
        print(f"분석용 영양제 상세 조회 중 서버 오류: {e}") 
        # db.session.rollback() # 필요 시 롤백 추가
        return jsonify({'ok': False, 'message': '서버 내부 오류로 영양제 정보를 불러올 수 없습니다.'}), 500

