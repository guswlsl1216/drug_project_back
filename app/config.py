import os
import secrets

class Config:
  SECRET_KEY = secrets.token_urlsafe(32)
  SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI')
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SQLALCHEMY_ECHO = True
  CORS_ORIGINS=["http://localhost:5173"]