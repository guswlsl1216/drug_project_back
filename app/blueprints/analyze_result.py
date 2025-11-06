from flask import Blueprint, jsonify, request
from app import db
from flask_login import current_user, login_required
from datetime import datetime

bp = Blueprint('analyze_result', __name__)

@bp.get('/test')
def test():
  return 'test'