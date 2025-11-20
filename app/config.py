import os
import secrets
from datetime import timedelta

class Config:
  SECRET_KEY = secrets.token_urlsafe(32)
  JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32)) # JWT전용
  SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI')
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SQLALCHEMY_ECHO = True
  CORS_ORIGINS=["http://localhost:5173"]
  UPLOAD_FOLDER = './uploads'

  # JWT 관련 설정
  JWT_TOKEN_LOCATION = ["cookies"] 
  JWT_ACCESS_COOKIE_PATH = "/"
  JWT_REFRESH_COOKIE_PATH = "/refresh"
  JWT_COOKIE_SECURE = False # 개발용 (후추 True로 전환 예정)
  JWT_COOKIE_SAMESITE = "Lax"
  JWT_COOKIE_CSRF_PROTECT = False
  JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2) # accessToken은 2시간
  JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7) # refreshToken은 7일

  # SESSION_COOKIE_SAMESITE = 'None'
  SESSION_COOKIE_SECURE = False

  # 토스 결제 시크릿 키 : 원래는 외부 공유 금지, 지금은 테스트용
  WIDGET_SECRET_KEY = "test_gsk_docs_OaPz8L5KdmQXkzRz3y47BMw6"

  MAIL_SERVER = os.environ.get('MAIL_SERVER')
  MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
  MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
  MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
  MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
  MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

