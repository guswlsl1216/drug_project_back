# 표준화 된 응답 포맷 
# API마다 JSON 구조가 다르면 프론트앤드 개발자는 헷갈리는 경우가 발생
from flask import jsonify

"""
표준화 된 API 응답을 생성하는 함수
"""
def make_response(ok=True, data=None, message='', status=200):
  return jsonify({
    'ok' : ok,
    'message' : message,
    'data' : data
  }), status