import logging
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from django.utils import timezone
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import json
from core.models import (
    WeatherDataLake, FloodPrediction, Ward, CrowdReport,
    HistoricalFloodEvent, ClimatePatternData, FloodHistoricalData
)

logger = logging.getLogger(__name__)

class HistoricalFloodMLModel:
    """Advanced ML model trained on 10 years of Nairobi flood data"""
    
    MODEL_PATH = Path(__file__).parent.parent / 'models' / 'historical_flood_model.pkl'
    SCALER_PATH = Path(__file__).parent.parent / 'models' / 'historical_scaler.pkl'
    
    @staticmethod
    def fetch_historical_training_data():
        """
        Fetch training data from:
        - HistoricalFloodEvent (2015-2025)
        - ClimatePatternData
        - Weather records
        """
        logger.info("Fetching historical training data (2015-2025)...")
        
        X = []
        y = []
        
        try:
            # Get all historical flood events
            flood_events = HistoricalFloodEvent.objects.all()
            logger.info(f"Found {flood_events.count()} historical flood events")
            
            # Training samples from historical events
            for event in flood_events:
                try:
                    # Get affected wards
                    affected_wards = event.affected_wards.all()
                    
                    for ward in affected_wards:
                        # Create feature vector
                        features = {
                            'rainfall': event.rainfall_mm,
                            'temperature': event.temperature_celsius or 25,
                            'humidity': event.humidity_percent or 60,
                            'wind_speed': event.wind_speed_kmh or 5,
                            'historical_avg_rainfall': 0,
                            'climate_pattern_score': 0,
                            'vulnerability_index': 0,
                            'month': event.date_occurred.month,
                        }
                        
                        # Get historical data for this ward
                        hist_data = FloodHistoricalData.objects.filter(
                            ward=ward,
                            year=event.date_occurred.year
                        ).first()
                        
                        if hist_data:
                            features['historical_avg_rainfall'] = hist_data.avg_rainfall_mm
                            features['vulnerability_index'] = hist_data.vulnerability_index
                        
                        # Map risk level to label
                        risk_map = {'Low': 0, 'Medium': 1, 'High': 2}
                        label = risk_map.get(event.risk_level, 1)
                        
                        X.append([
                            features['rainfall'],
                            features['temperature'],
                            features['humidity'],
                            features['wind_speed'],
                            features['historical_avg_rainfall'],
                            features['climate_pattern_score'],
                            features['vulnerability_index'],
                            features['month'],
                        ])
                        y.append(label)
                
                except Exception as e:
                    logger.error(f"Error processing flood event: {str(e)}")
                    continue
            
            # Add climate pattern data
            climate_data = ClimatePatternData.objects.all()
            for climate in climate_data:
                try:
                    features = [
                        climate.avg_rainfall_mm,
                        climate.avg_temperature_celsius,
                        climate.avg_humidity_percent,
                        0,  # wind speed (not in climate data)
                        climate.avg_rainfall_mm,
                        climate.flood_probability * 100,
                        0,  # vulnerability
                        climate.month,
                    ]
                    
                    label = 2 if climate.has_flood_occurred else 0
                    X.append(features)
                    y.append(label)
                
                except Exception as e:
                    logger.error(f"Error processing climate data: {str(e)}")
                    continue
            
            X = np.array(X)
            y = np.array(y)
            
            logger.info(f"Historical training dataset prepared: {len(X)} samples")
            logger.info(f"Class distribution: {np.bincount(y)}")
            
            return X, y
        
        except Exception as e:
            logger.error(f"Error fetching historical training data: {str(e)}")
            return np.array([]), np.array([])
    
    @staticmethod
    def train_historical_model(force=False):
        """Train model on 10 years of historical flood data"""
        try:
            if HistoricalFloodMLModel.MODEL_PATH.exists() and not force:
                logger.info("Historical model already exists")
                return True
            
            HistoricalFloodMLModel.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # Fetch historical data
            X, y = HistoricalFloodMLModel.fetch_historical_training_data()
            
            if len(X) < 10:
                logger.warning(f"Insufficient training data: {len(X)} samples")
                return False
            
            logger.info(f"Training on {len(X)} historical samples...")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Ensemble model
            rf_model = RandomForestClassifier(
                n_estimators=300,
                max_depth=20,
                min_samples_split=3,
                min_samples_leaf=1,
                random_state=42,
                class_weight='balanced_subsample',
                n_jobs=-1
            )
            
            gb_model = GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=12,
                min_samples_split=3,
                min_samples_leaf=1,
                random_state=42,
                subsample=0.8
            )
            
            ensemble_model = VotingClassifier(
                estimators=[('rf', rf_model), ('gb', gb_model)],
                voting='soft',
                weights=[0.6, 0.4]  # RF weighted more
            )
            
            # Train
            ensemble_model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = ensemble_model.predict(X_test_scaled)
            y_pred_proba = ensemble_model.predict_proba(X_test_scaled)
            
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            
            try:
                roc_auc = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
            except:
                roc_auc = 0.0
            
            logger.info(f"Model Performance (10-Year Historical Data):")
            logger.info(f"  Accuracy:  {accuracy:.2%}")
            logger.info(f"  Precision: {precision:.2%}")
            logger.info(f"  Recall:    {recall:.2%}")
            logger.info(f"  F1 Score:  {f1:.2%}")
            logger.info(f"  ROC-AUC:   {roc_auc:.2%}")
            
            # Save
            with open(HistoricalFloodMLModel.MODEL_PATH, 'wb') as f:
                pickle.dump(ensemble_model, f)
            
            with open(HistoricalFloodMLModel.SCALER_PATH, 'wb') as f:
                pickle.dump(scaler, f)
            
            logger.info("Historical flood model trained and saved")
            return True
        
        except Exception as e:
            logger.error(f"Error training historical model: {str(e)}")
            return False
    
    @staticmethod
    def predict_with_historical_context(ward):
        """Predict flood risk with historical context"""
        try:
            if not HistoricalFloodMLModel.MODEL_PATH.exists():
                logger.warning("Historical model not found")
                return None
            
            # Prepare features
            features = HistoricalFloodMLModel.prepare_enhanced_features(ward)
            
            if not features:
                return None
            
            # Load model
            with open(HistoricalFloodMLModel.MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            
            with open(HistoricalFloodMLModel.SCALER_PATH, 'rb') as f:
                scaler = pickle.load(f)
            
            # Predict
            feature_array = np.array([features]).reshape(1, -1)
            feature_scaled = scaler.transform(feature_array)
            
            risk_proba = model.predict_proba(feature_scaled)[0]
            risk_pred = model.predict(feature_scaled)[0]
            confidence = np.max(risk_proba)
            
            risk_levels = ['Low', 'Medium', 'High']
            risk_level = risk_levels[risk_pred]
            
            return {
                'risk_level': risk_level,
                'confidence': float(confidence),
                'probabilities': {
                    'Low': float(risk_proba[0]),
                    'Medium': float(risk_proba[1]) if len(risk_proba) > 1 else 0,
                    'High': float(risk_proba[2]) if len(risk_proba) > 2 else 0
                }
            }
        
        except Exception as e:
            logger.error(f"Error in prediction: {str(e)}")
            return None
    
    @staticmethod
    def prepare_enhanced_features(ward):
        """Prepare features with historical context"""
        try:
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            
            # Current weather
            weather = WeatherDataLake.objects.filter(
                ward=ward,
                timestamp__gte=last_24h
            ).last()
            
            rainfall = weather.rainfall_mm if weather and weather.rainfall_mm else 0
            temperature = weather.temperature_celsius if weather and weather.temperature_celsius else 25
            humidity = weather.humidity_percent if weather and weather.humidity_percent else 60
            wind_speed = weather.wind_speed_kmh if weather and weather.wind_speed_kmh else 5
            
            # Historical data
            hist_data = FloodHistoricalData.objects.filter(
                ward=ward,
                year=now.year
            ).first()
            
            historical_avg = hist_data.avg_rainfall_mm if hist_data else 0
            vulnerability = hist_data.vulnerability_index if hist_data else 0
            
            # Climate pattern
            climate = ClimatePatternData.objects.filter(
                ward=ward,
                month=now.month
            ).order_by('-year').first()
            
            flood_probability = (climate.flood_probability * 100) if climate else 0
            
            return [
                rainfall,
                temperature,
                humidity,
                wind_speed,
                historical_avg,
                flood_probability,
                vulnerability,
                now.month,
            ]
        
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            return None
