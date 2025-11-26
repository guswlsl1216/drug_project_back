from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import tensorflow as tf
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("2tle/korean-curse-detection")
model = AutoModelForSequenceClassification.from_pretrained("2tle/korean-curse-detection")

# 객체 생성 해줌 
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cors = CORS()
jwt = JWTManager()