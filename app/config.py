import os
import secrets

class Config:
  SECRET_KEY = secrets.token_urlsafe(32)
  JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32)) # JWT전용
  SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI')
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SQLALCHEMY_ECHO = True
  CORS_ORIGINS=["http://localhost:5173"]
  UPLOAD_FOLDER = './uploads'
  JWT_ACCESS_EXPIRES = 7200 #2시간