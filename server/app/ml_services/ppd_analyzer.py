import joblib
from pathlib import Path

class PPDAnalyzer:
    def __init__(self, model_version="latest"):
        model_dir = Path(__file__).resolve().parent.parent.parent / "ml" / "models"
        
        if model_version == "latest":
            model_files = list(model_dir.glob("ppd_model_v*.pkl"))
            model_path = max(model_files, key=lambda x: x.stat().st_mtime)
        else:
            model_path = model_dir / f"ppd_model_v{model_version}.pkl"
            
        self.model = joblib.load(model_path)
        print(f"✅ Loaded model: {model_path.name}")

    def predict(self, input_data):
        return self.model.predict_proba([input_data])[0][1]  # Returns PPD probability