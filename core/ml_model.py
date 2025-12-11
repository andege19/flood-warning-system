# Enhanced ML Model for Flood Risk Prediction
import logging
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from django.utils import timezone
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
from core.models import WeatherDataLake, FloodPrediction, Ward, CrowdReport

logger = logging.getLogger(__name__)

class FloodRiskMLModel:
    """Enhanced ML model for flood risk prediction"""
    
    MODEL_PATH = Path(__file__).parent.parent / 'models' / 'flood_risk_model.pkl'
    SCALER_PATH = Path(__file__).parent.parent / 'models' / 'feature_scaler.pkl'
    
    # Risk thresholds
    HIGH_RISK_THRESHOLD = 0.7
    MEDIUM_RISK_THRESHOLD = 0.4
    
    @staticmethod
    def prepare_features_for_ward(ward):
        """
        Prepare features for a specific ward
        
        Features:
        1. Recent rainfall (24h average)
        2. Rainfall trend (24h change)
        3. Historical average rainfall
        4. Temperature (current)
        5. Humidity (current)
        6. Wind speed (current)
        7. Community report count (last 7 days)
        8. Community report severity (average)
        """
        try:
            features = {}
            
            # Get last 24 hours of weather data
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            weather_data_24h = WeatherDataLake.objects.filter(
                ward=ward,
                timestamp__gte=last_24h
            ).order_by('timestamp')
            
            weather_data_all = WeatherDataLake.objects.filter(
                ward=ward
            ).order_by('timestamp')
            
            # Feature 1: Recent rainfall (24h average)
            rainfall_24h = [w.rainfall_mm for w in weather_data_24h if w.rainfall_mm]
            features['rainfall_24h_avg'] = np.mean(rainfall_24h) if rainfall_24h else 0
            
            # Feature 2: Rainfall trend
            if len(rainfall_24h) > 1:
                first_half = rainfall_24h[:len(rainfall_24h)//2]
                second_half = rainfall_24h[len(rainfall_24h)//2:]
                features['rainfall_trend'] = np.mean(second_half) - np.mean(first_half)
            else:
                features['rainfall_trend'] = 0
            
            # Feature 3: Historical average rainfall
            historical_rainfall = [w.rainfall_mm for w in weather_data_all if w.rainfall_mm]
            features['rainfall_historical_avg'] = np.mean(historical_rainfall) if historical_rainfall else 0
            
            # Feature 4: Current temperature
            latest_weather = weather_data_24h.last()
            features['temperature'] = latest_weather.temperature_celsius if latest_weather and latest_weather.temperature_celsius else 20
            
            # Feature 5: Current humidity
            features['humidity'] = latest_weather.humidity_percent if latest_weather and latest_weather.humidity_percent else 50
            
            # Feature 6: Wind speed
            features['wind_speed'] = latest_weather.wind_speed_kmh if latest_weather and latest_weather.wind_speed_kmh else 0
            
            # Feature 7: Community report count (last 7 days)
            community_reports = CrowdReport.objects.filter(
                ward=ward,
                created_at__gte=last_7d,
                status='Validated'
            ).count()
            features['validated_reports_7d'] = community_reports
            
            # Feature 8: Community report severity average
            reports = CrowdReport.objects.filter(
                ward=ward,
                created_at__gte=last_7d,
                status='Validated'
            )
            if reports.exists():
                # Severity based on report count and reliability
                severity_scores = []
                for report in reports:
                    severity = min(10, report.reliability_score * 10 + report.upvotes)
                    severity_scores.append(severity)
                features['report_severity_avg'] = np.mean(severity_scores)
            else:
                features['report_severity_avg'] = 0
            
            logger.info(f"Features prepared for {ward.name}: {features}")
            return features
        
        except Exception as e:
            logger.error(f"Error preparing features for {ward.name}: {str(e)}")
            return None
    
    @staticmethod
    def predict_risk_for_ward(ward):
        """
        Predict flood risk for a specific ward
        
        Returns:
            dict: {
                'risk_level': 'High'|'Medium'|'Low',
                'probability': float (0-1),
                'probabilities': {'Low': ..., 'Medium': ..., 'High': ...},
                'confidence': float (0-1),
                'features_used': dict
            }
        """
        try:
            # Prepare features
            features = FloodRiskMLModel.prepare_features_for_ward(ward)
            if not features:
                logger.warning(f"Could not prepare features for {ward.name}")
                return None
            
            # Convert to array in correct order
            feature_array = np.array([
                features['rainfall_24h_avg'],
                features['rainfall_trend'],
                features['rainfall_historical_avg'],
                features['temperature'],
                features['humidity'],
                features['wind_speed'],
                features['validated_reports_7d'],
                features['report_severity_avg']
            ]).reshape(1, -1)
            
            # Load model and scaler
            if not FloodRiskMLModel.MODEL_PATH.exists():
                logger.warning(f"Model not found at {FloodRiskMLModel.MODEL_PATH}, using baseline")
                return FloodRiskMLModel._baseline_prediction(ward, features)
            
            with open(FloodRiskMLModel.MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            
            with open(FloodRiskMLModel.SCALER_PATH, 'rb') as f:
                scaler = pickle.load(f)
            
            # Scale features
            feature_scaled = scaler.transform(feature_array)
            
            # Predict
            risk_proba = model.predict_proba(feature_scaled)[0]
            risk_pred = model.predict(feature_scaled)[0]
            confidence = np.max(risk_proba)
            
            # Map prediction to risk level
            risk_levels = ['Low', 'Medium', 'High']
            risk_level = risk_levels[risk_pred]
            
            # Build probability dict
            probabilities = {
                'Low': float(risk_proba[0]),
                'Medium': float(risk_proba[1]),
                'High': float(risk_proba[2])
            }
            
            logger.info(f"Prediction for {ward.name}: {risk_level} (confidence: {confidence:.2f})")
            
            return {
                'risk_level': risk_level,
                'probability': float(probabilities[risk_level]),
                'probabilities': probabilities,
                'confidence': float(confidence),
                'features_used': features
            }
        
        except Exception as e:
            logger.error(f"Error predicting risk for {ward.name}: {str(e)}")
            return FloodRiskMLModel._baseline_prediction(ward, None)
    
    @staticmethod
    def _baseline_prediction(ward, features):
        """Fallback baseline prediction if model not available"""
        try:
            if not features:
                features = FloodRiskMLModel.prepare_features_for_ward(ward)
            
            # Simple rule-based prediction
            rainfall = features.get('rainfall_24h_avg', 0)
            reports = features.get('validated_reports_7d', 0)
            
            risk_score = (rainfall / 50.0) * 0.6 + (reports / 10.0) * 0.4
            risk_score = min(1.0, max(0.0, risk_score))
            
            if risk_score >= FloodRiskMLModel.HIGH_RISK_THRESHOLD:
                risk_level = 'High'
            elif risk_score >= FloodRiskMLModel.MEDIUM_RISK_THRESHOLD:
                risk_level = 'Medium'
            else:
                risk_level = 'Low'
            
            return {
                'risk_level': risk_level,
                'probability': risk_score,
                'probabilities': {
                    'Low': max(0, 1 - risk_score),
                    'Medium': max(0, risk_score - 0.4) if risk_score >= 0.4 else 0,
                    'High': max(0, risk_score - 0.7) if risk_score >= 0.7 else 0
                },
                'confidence': 0.5,
                'features_used': features,
                'method': 'baseline'
            }
        except Exception as e:
            logger.error(f"Baseline prediction failed: {str(e)}")
            return None
    
    @staticmethod
    def train_model(force=False):
        """
        Train model on historical weather data
        
        Args:
            force (bool): Force retraining even if model exists
        """
        try:
            if FloodRiskMLModel.MODEL_PATH.exists() and not force:
                logger.info("Model already exists, skipping training")
                return True
            
            # Ensure models directory exists
            FloodRiskMLModel.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # For now, use a simple trained model
            # In production, you would train on real historical data
            X_train = np.array([
                [10, 5, 8, 25, 60, 10, 2, 5],
                [5, 2, 6, 28, 50, 5, 0, 0],
                [30, 15, 20, 22, 80, 15, 5, 7],
                [2, 1, 3, 30, 40, 2, 0, 0],
                [25, 12, 18, 20, 75, 12, 3, 4],
            ])
            
            y_train = np.array([1, 0, 2, 0, 1])
            
            # Scale
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_train)
            
            # Train
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            model.fit(X_scaled, y_train)
            
            # Save
            with open(FloodRiskMLModel.MODEL_PATH, 'wb') as f:
                pickle.dump(model, f)
            
            with open(FloodRiskMLModel.SCALER_PATH, 'wb') as f:
                pickle.dump(scaler, f)
            
            logger.info("Model trained and saved")
            return True
        
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False
    
    @staticmethod
    def predict_all_wards():
        """Predict flood risk for all wards"""
        try:
            wards = Ward.objects.all()
            predictions_created = 0
            
            for ward in wards:
                prediction = FloodRiskMLModel.predict_risk_for_ward(ward)
                
                if prediction:
                    now = timezone.now()
                    FloodPrediction.objects.create(
                        ward=ward,
                        predicted_risk_level=prediction['risk_level'],
                        confidence_score=prediction['confidence'],
                        probability_low=prediction['probabilities']['Low'],
                        probability_medium=prediction['probabilities']['Medium'],
                        probability_high=prediction['probabilities']['High'],
                        features_used=prediction['features_used'],
                        model_version='v2.0',
                        valid_from=now,
                        valid_until=now + timedelta(hours=2)
                    )
                    predictions_created += 1
                    
                    # Update ward
                    ward.current_risk_level = prediction['risk_level']
                    ward.save()
            
            logger.info(f"Predictions created: {predictions_created}")
            return predictions_created
        
        except Exception as e:
            logger.error(f"Error predicting all wards: {str(e)}")
            return 0