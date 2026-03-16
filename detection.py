import onnxruntime as ort
from ultralytics import YOLO
import os
from config import config
import torch

_original_session = None

def _apply_directml_monkey_patch():
    """Global monkey patch to force Ultralytics to use DirectML execution provider."""
    global _original_session
    if _original_session is not None:
        return
    
    _original_session = ort.InferenceSession
    
    def patched_session(*args, **kwargs):
        kwargs['providers'] = ['DmlExecutionProvider', 'CPUExecutionProvider']
        return _original_session(*args, **kwargs)
    
    ort.InferenceSession = patched_session
    print("[INFO] Applied DirectML monkey patch for ONNX Runtime")

_model = None
_class_names = {}
_model_imgsz = None

if torch.cuda.is_available():
    DEVICE = 0               
else:
    DEVICE = "cpu"

def load_model(model_path=None):
    global _model, _class_names, _model_imgsz
    if model_path is None:
        model_path = config.model_path
    try:
        _apply_directml_monkey_patch()
        
        _model = YOLO(model_path, task="detect")
        
        if hasattr(_model, "names"):
            _class_names = _model.names
        elif hasattr(_model.model, "names"):
            _class_names = _model.model.names
        else:
            _class_names = {}
            config.model_load_error = "Class names not found"
        
        config.model_classes = list(_class_names.values())
        config.model_file_size = os.path.getsize(model_path) if os.path.exists(model_path) else 0
        config.model_load_error = ""
        
        native_imgsz = None
        try:
            if hasattr(_model, 'model') and hasattr(_model.model, 'args'):
                args_imgsz = _model.model.args.get('imgsz')
                if args_imgsz is not None:
                    if isinstance(args_imgsz, (list, tuple)):
                        native_imgsz = max(args_imgsz)
                    else:
                        native_imgsz = int(args_imgsz)
            
            if native_imgsz is None and hasattr(_model.model, 'imgsz'):
                imgsz_val = _model.model.imgsz
                if isinstance(imgsz_val, (list, tuple)):
                    native_imgsz = int(imgsz_val[0])
                else:
                    native_imgsz = int(imgsz_val)
            
            if native_imgsz is None and hasattr(_model, 'args'):
                args_imgsz = _model.args.get('imgsz')
                if args_imgsz is not None:
                    if isinstance(args_imgsz, (list, tuple)):
                        native_imgsz = max(args_imgsz)
                    else:
                        native_imgsz = int(args_imgsz)
        except Exception as e:
            print(f"[WARNING] Could not auto-detect model imgsz: {e}, using config.imgsz={config.imgsz}")
        
        if native_imgsz is not None:
            _model_imgsz = native_imgsz
            config.imgsz = native_imgsz
            print(f"[INFO] Auto-detected model native imgsz: {native_imgsz}")
        else:
            _model_imgsz = int(config.imgsz)
            print(f"[INFO] Using config imgsz: {_model_imgsz}")
        
        return _model, _class_names
    except Exception as e:
        config.model_load_error = f"Failed to load model: {e}"
        _model = None
        _class_names = {}
        _model_imgsz = None
        return None, {}

def reload_model(model_path):
    return load_model(model_path)

def perform_detection(model, image):
    """Perform object detection on an image using the loaded model."""
    global _model_imgsz
    if model is None:
        print("[WARN] Model is None, cannot perform detection. Please check model loading.")
        return None
    
    try:
        imgsz_to_use = _model_imgsz if _model_imgsz is not None else int(config.imgsz)
        
        results = model.predict(
            source=image,
            imgsz=imgsz_to_use,
            stream=True,
            conf=config.conf,
            iou=0.45,
            device=DEVICE,
            half=True,
            max_det=5,
            agnostic_nms=False,
            augment=False,
            vid_stride=False,
            visualize=False,
            verbose=False,
            show_boxes=False,
            show_labels=False,
            show_conf=False,
            save=False,
            show=False
        )
        return results
    except Exception as e:
        print(f"[ERROR] Detection failed: {e}")
        return None

def get_class_names():
    return _class_names

def get_model_size(model_path=None):
    if not model_path:
        model_path = config.model_path
    return os.path.getsize(model_path) if os.path.exists(model_path) else 0
