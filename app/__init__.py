from flask import Flask
from .extensions import db, migrate, login_manager, cors, jwt
from .config import Config


def create_app():
  app = Flask(__name__)
  app.config.from_object(Config)

  # 최대 5MB
  app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
  # /static/uploads 아래에 저장 (current_app.static_folder 사용)
  app.config["UPLOAD_SUBDIR"] = "uploads"
  app.config["UPLOAD_REVIEW_IMAGE"] = "review"

  db.init_app(app)
  jwt.init_app(app)
  migrate.init_app(app, db)
  cors.init_app(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)
  login_manager.init_app(app)
  
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
<<<<<<< HEAD
  from .blueprints.user_cart import bp as cart_bp
=======
  from .blueprints.payments import bp as payments_bp
  from .blueprints.order import bp as order_bp
  from .blueprints.inquiry import bp as inquiry_bp
  from .blueprints.qna import bp as qna_bp

>>>>>>> develop
  


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
<<<<<<< HEAD
  app.register_blueprint(cart_bp, url_prefix='/cart')
=======
  app.register_blueprint(payments_bp, url_prefix='/payments')
  app.register_blueprint(order_bp, url_prefix='/orders')
  app.register_blueprint(inquiry_bp, url_prefix='/inquiry')
  app.register_blueprint(qna_bp, url_prefix='/qna')
>>>>>>> develop

  return app