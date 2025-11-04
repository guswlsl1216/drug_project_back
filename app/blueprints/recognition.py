import torch
from flask import Blueprint, request, jsonify
from PIL import Image
import io
import os
import sys
import importlib.util
import numpy as np


BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', '..', '..')) # teamproject
YOLOV5_REPO_PATH = os.path.join(PROJECT_ROOT, 'drug_project_ai', 'yolov5') # YOLOv5 깃 클론 폴더 경로
CONF_THRESHOLD = 0.50 # 탐지 결과를 출력할 최소 신뢰도
TRAIN_FOLDER_NAME = 'drug_recognition_v4'
MODEL_PATH = os.path.join(YOLOV5_REPO_PATH, 'runs', 'train', TRAIN_FOLDER_NAME, 'weights', 'best.pt')

sys.path.append(YOLOV5_REPO_PATH)

bp = Blueprint('recognition', __name__)

model = None
DEVICE = torch.device('cpu')

# 파일 경로로부터 모듈을 동적으로 로드해서 반환
def _load_module_from_path(name, path):
  spec = importlib.util.spec_from_file_location(name, path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module

# 서버 연결 확인용
print("🔍 YOLOV5_REPO_PATH:", YOLOV5_REPO_PATH)
print("📁 common.py exists:", os.path.isfile(os.path.join(YOLOV5_REPO_PATH, 'models', 'common.py')))
print("📁 torch_utils.py exists:", os.path.isfile(os.path.join(YOLOV5_REPO_PATH, 'utils', 'torch_utils.py')))

# Flask 앱이 초기화될 때 모델을 로드하는 함수
def load_recognition_model():
  global model, DEVICE

  DEVICE = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
  print(f"Loading YOLOv5 Model on {DEVICE}...")

  try:
    models_common_path = os.path.join(YOLOV5_REPO_PATH, 'models', 'common.py')
    torch_utils_path = os.path.join(YOLOV5_REPO_PATH, 'utils', 'torch_utils.py')

    if not os.path.isfile(models_common_path) or not os.path.isfile(torch_utils_path):
        raise FileNotFoundError(f"Missing YOLOv5 files: {models_common_path} or {torch_utils_path}")

    models_common = _load_module_from_path('yolov5_models_common', models_common_path)
    torch_utils = _load_module_from_path('yolov5_utils_torch', torch_utils_path)

    DetectMultiBackend = getattr(models_common, 'DetectMultiBackend')
    select_device = getattr(torch_utils, 'select_device')

    device = select_device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model = DetectMultiBackend(MODEL_PATH, device=device)
    model.model.eval() if hasattr(model, 'model') else model.eval()

    print(f"YOLOv5 Model loaded successfully on {device}")
  except Exception as e:
    print(f"Error loading model: {e}")
    model = None


# 업로드된 이미지 파일을 전처리하고 YOLOv5 모델로 추론을 수행
@bp.route('/predict', methods=['POST'])
def predict():
  if model is None:
      return jsonify({"error":"Model service is temporarily unavailable."}), 500
  
  if 'file' not in request.files:
    return jsonify({"error":"No 'file' key in the request"}), 400
  
  file = request.files['file']

  if file.filename == '':
    return jsonify({"error": "No selected file"}), 400
    
  try:
    img_bytes = file.read()
    img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    img = np.array(img) # numpy 배열로 변환
    results = model(img)

    results = model(img)
    df = results.pandas().xyxy[0] # 탐지된 객체들의 정보를 담은 프레임
    detections = []

    for _, row in df.iterrows():
      if row['confidence'] >= CONF_THRESHOLD:
        detections.append({
          "drug_code":row['name'],
          "confidence":round(row['confidence'], 4),
          "bbox":[int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])]
      })
    
    return jsonify({"detections": detections, "count":len(detections)}), 200 # 탐지된 약물 정보와 개수를 반환

  except Exception as e:
    print(f"Prediction Error: {e}")
    return jsonify({"error":f"An unexpected error occurred during prediction: {str(e)}"}), 500
  