import os
import datetime
from flask import Flask, jsonify, current_app
from flask_mail import Mail
from .extensions import db, migrate, login_manager, cors, jwt
from .config import Config
from flask_apscheduler import APScheduler

mail = Mail()
scheduler = APScheduler()

def daily_cleanup(app):
  """
  서버의 임시 폴더(static/temp)에서 24시간 이상 지난 파일을 삭제합니다.
  """
  with app.app_context():
    temp_dir = os.path.join(current_app.root_path, 'static', 'temp')

    if not os.path.exists(temp_dir):
      print(f"[{datetime.datetime.now()}] 임시 이미지 폴더가 존재하지 않아 정리 건너뜀.")
      return
    
    cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=24)
    deleted_count = 0

    for filename in os.listdir(temp_dir):
      file_path = os.path.join(temp_dir, filename)

      if os.path.isfile(file_path):
        file_modified_time_timestamp = os.path.getmtime(file_path)
        file_modified_time = datetime.datetime.fromtimestamp(file_modified_time_timestamp)

        if file_modified_time < cutoff_time:
          try:
            os.remove(file_path)
            deleted_count += 1
          except Exception as e:
            print(f"[{datetime.datetime.now()}] 파일 삭제 실패 ({file_path}): {e}")

    print(f"[{datetime.datetime.now()}] 임시 폴더 정리 완료. 삭제된 파일 수: {deleted_count}개")

def create_app():
  app = Flask(__name__)
  app.config.from_object(Config)

  # 최대 5MB
  app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
  # /static/uploads 아래에 저장 (current_app.static_folder 사용)
  app.config["UPLOAD_SUBDIR"] = "uploads"
  app.config["UPLOAD_REVIEW_IMAGE"] = "review"
  app.config["UPLOAD_ANALYZE"] = "analyze"
  app.config["UPLOAD_TEMP"] = "temp"

  db.init_app(app)
  jwt.init_app(app)
  migrate.init_app(app, db)
  cors.init_app(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)
  login_manager.init_app(app)
  mail.init_app(app)
  scheduler.init_app(app)

  @jwt.unauthorized_loader
  def handle_missing_or_invalid_token(err):
    """
    JWT 토큰이 없거나 유효하지 않아 401 Unauthorized 에러가 발생할 때 호출됩니다.
    """
    # HTTP 401 상태 코드와 함께 원하는 메시지를 반환합니다.
    return jsonify({
      'ok': False,
      'message': '로그인 후 이용하십시오.' 
    }), 401
  
  @jwt.user_lookup_loader
  def user_lookup_callback(_jwt_header, jwt_payload):
    from .models.user import User
    identity = jwt_payload["sub"]
    return User.query.get(int(identity))

  with app.app_context():
    db.create_all()
    from .models import auto as auto_models
    auto_models.prepare_automap(only={
      "supps_products", "meds_products", 
      "drug_contraindications", "supps_meds_interaction"
    })

  from .blueprints.routine import bp as routine_bp
  from .blueprints.user_drugs import bp as user_drugs_bp
  from .blueprints.user_meds import bp as user_meds_bp
  from .blueprints.auth import bp as auth_bp
  from .blueprints.login import bp as login_bp
  from .blueprints.protected import bp as protected_bp
  from .blueprints.goods import bp as goods_bp
  from .blueprints.favorite import bp as favorite_bp
  from .blueprints.analyze_result import bp as analyze_result_bp
  from .blueprints.aiAnalyze import bp as aiAnalyze_bp
  from .blueprints.admin import bp as admin_bp
  from .blueprints.review import bp as review_bp
  from .blueprints.user_cart import bp as cart_bp
  from .blueprints.payments import bp as payments_bp
  from .blueprints.order import bp as order_bp
  from .blueprints.inquiry import bp as inquiry_bp
  from .blueprints.qna import bp as qna_bp

  


  app.register_blueprint(routine_bp, url_prefix='/routine')
  app.register_blueprint(user_drugs_bp, url_prefix='/user_drugs')
  app.register_blueprint(user_meds_bp, url_prefix='/user_meds')
  app.register_blueprint(auth_bp, url_prefix='/auth')
  app.register_blueprint(login_bp, url_prefix='/login')
  app.register_blueprint(protected_bp, url_prefix='/user_protected')
  app.register_blueprint(goods_bp, url_prefix='/goods')
  app.register_blueprint(favorite_bp, url_prefix='/favorite')
  app.register_blueprint(analyze_result_bp, url_prefix='/result')
  app.register_blueprint(aiAnalyze_bp, url_prefix='/aiAnalyze')
  app.register_blueprint(admin_bp, url_prefix='/admin')
  app.register_blueprint(review_bp, url_prefix='/review')
  app.register_blueprint(cart_bp, url_prefix='/cart')
  app.register_blueprint(payments_bp, url_prefix='/payments')
  app.register_blueprint(order_bp, url_prefix='/orders')
  app.register_blueprint(inquiry_bp, url_prefix='/inquiry')
  app.register_blueprint(qna_bp, url_prefix='/qna')


  # 스케줄러 시작
  if not scheduler.running:
    scheduler.start()
  
  # temp 파일 삭제 스케줄러 등록
  # 현재 기준 : 오전 9시 40분 실행
  if not scheduler.get_job('temp_cleanup_job'):
    scheduler.add_job(
      id='temp_cleanup_job',
      func=daily_cleanup,
      trigger='cron',
      hour=9,
      minute=40,
      args=[app],
      replace_existing=True
    )
    
  return app