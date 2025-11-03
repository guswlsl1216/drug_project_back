from flask import Flask
from .extensions import db, migrate, login_manager, cors
from .config import Config


def create_app():
  app = Flask(__name__)
  app.config.from_object(Config)

  db.init_app(app)
  migrate.init_app(app, db)
  cors.init_app(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)
  login_manager.init_app(app)

  with app.app_context():
    from .models import auto as auto_models
    auto_models.prepare_automap(only={
      "health_products", "drug_products", 
      "drug_contraindications", "health_drug_interaction"
    })

  from .blueprints.routine import bp as routine_bp
  from .blueprints.user_meds import bp as user_meds_bp
  from .blueprints.auth import bp as auth_bp

  app.register_blueprint(routine_bp, url_prefix='/routine')
  app.register_blueprint(user_meds_bp, url_prefix='/user_meds')
  app.register_blueprint(auth_bp, url_prefix='/auth')

  return app