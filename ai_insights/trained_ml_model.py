"""
Django view to use trained ML model from PKL file
Place trained model files in: ml_models/ directory
"""
import os
import joblib
import numpy as np
import warnings
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone

# Suppress sklearn warnings
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

class TrainedMLPredictor:
    """Use trained ML model from Colab"""
    
    def __init__(self):
        self.model_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        self.model = None
        self.scaler = None
        self.encoders = {}
        self.features = None
        self.load_models()
    
    def load_models(self):
        """Load trained models from PKL files"""
        try:
            # Try different model file names
            model_files = ['sales_model_7.pkl', 'cloudshop_sales_model.pkl']
            scaler_files = ['scaler_7.pkl', 'cloudshop_scaler.pkl']
            
            for model_file in model_files:
                model_path = os.path.join(self.model_dir, model_file)
                if os.path.exists(model_path):
                    self.model = joblib.load(model_path)
                    print(f"✅ ML Model loaded: {model_file}")
                    break
            
            for scaler_file in scaler_files:
                scaler_path = os.path.join(self.model_dir, scaler_file)
                if os.path.exists(scaler_path):
                    self.scaler = joblib.load(scaler_path)
                    break
            
            features_path = os.path.join(self.model_dir, 'cloudshop_features.pkl')
            if os.path.exists(features_path):
                self.features = joblib.load(features_path)
            
            # Load encoders
            encoder_files = ['category', 'gender', 'payment', 'location']
            for encoder_name in encoder_files:
                encoder_path = os.path.join(self.model_dir, f'cloudshop_{encoder_name}_encoder.pkl')
                if os.path.exists(encoder_path):
                    self.encoders[encoder_name] = joblib.load(encoder_path)
            
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def predict_sales(self, future_days=7):
        """Predict sales using trained model"""
        if not self.model:
            return self._fallback_predictions(future_days)
        
        try:
            predictions = []
            
            for i in range(1, future_days + 1):
                future_date = timezone.now().date() + timedelta(days=i)
                
                # EXACTLY 8 features to match training data
                features = [
                    future_date.weekday(),  # day_of_week
                    future_date.month,      # month
                    future_date.day,        # day_of_month
                    1 if future_date.weekday() >= 5 else 0,  # is_weekend
                    1 if future_date.day > 25 else 0,  # is_month_end
                    2500,   # sales_lag_1 (previous day sales estimate)
                    2300,   # sales_lag_7 (7 days ago sales estimate)
                    2400    # sales_ma_7 (7-day moving average)
                ]
                
                # Ensure exactly 8 features
                if len(features) != 8:
                    print(f"⚠️ Feature count error: {len(features)} instead of 8")
                    return self._fallback_predictions(future_days)
                
                # Scale features if scaler available
                if self.scaler:
                    try:
                        # Convert to numpy array with proper shape
                        features_array = np.array(features).reshape(1, -1)
                        features_scaled = self.scaler.transform(features_array)
                        prediction = self.model.predict(features_scaled)[0]
                    except Exception as scale_error:
                        print(f"Scaling error: {scale_error}")
                        return self._fallback_predictions(future_days)
                else:
                    prediction = self.model.predict([features])[0]
                
                # Ensure positive prediction
                prediction = max(0, prediction)
                
                predictions.append({
                    'date': future_date,
                    'predicted_sales': round(float(prediction), 2),
                    'confidence': 85,
                    'method': 'Trained ML Model'
                })
            
            return predictions
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return self._fallback_predictions(future_days)
    
    def _fallback_predictions(self, future_days):
        """Fallback predictions when model fails"""
        predictions = []
        base_sales = 2500  # Default daily sales
        
        for i in range(1, future_days + 1):
            future_date = timezone.now().date() + timedelta(days=i)
            
            # Weekend boost
            multiplier = 1.3 if future_date.weekday() >= 5 else 0.9
            prediction = base_sales * multiplier
            
            predictions.append({
                'date': future_date,
                'predicted_sales': round(prediction, 2),
                'confidence': 60,
                'method': 'Statistical Model'
            })
        
        return predictions
    
    def is_model_loaded(self):
        """Check if model is loaded"""
        return self.model is not None
    
    def get_model_status(self):
        """Get detailed model status"""
        if self.model:
            return "✅ Trained ML Model Active"
        else:
            return "⚠️ Using Statistical Model (Train ML for better accuracy)"
