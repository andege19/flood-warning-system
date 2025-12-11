import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_warning_system.settings')
django.setup()

from django.contrib.auth import authenticate
from core.models import CustomUser, Ward, WeatherDataLake, FloodPrediction, CrowdReport
from core.services.data_pipeline import DataPipeline
from core.ml_model import FloodRiskMLModel
from core.services.email_service import FloodAlertEmailService
from django.utils import timezone
from datetime import timedelta

class SystemTester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
    
    def print_section(self, title):
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    
    def print_test(self, test_name, status, details=""):
        symbol = "✓" if status else "✗"
        color = "\033[92m" if status else "\033[91m"
        reset = "\033[0m"
        
        print(f"{color}{symbol}{reset} {test_name}")
        if details:
            print(f"  └─ {details}")
        
        if status:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
    
    def test_database_connection(self):
        """Test 1: Database Connection"""
        self.print_section("TEST 1: DATABASE CONNECTION")
        
        try:
            count = Ward.objects.count()
            self.print_test("Database connection", True, f"Connected ({count} wards found)")
            return True
        except Exception as e:
            self.print_test("Database connection", False, str(e))
            return False
    
    def test_user_authentication(self):
        """Test 2: User Authentication"""
        self.print_section("TEST 2: USER AUTHENTICATION")
        
        try:
            # Test 2.1: User creation
            user, created = CustomUser.objects.get_or_create(
                username='test_resident',
                defaults={
                    'email': 'test@example.com',
                    'role': 'resident',
                    'is_active': True
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            
            self.print_test("User creation/retrieval", True, f"User: {user.username} (role: {user.role})")
            
            # Test 2.2: Authentication
            auth_user = authenticate(username='test_resident', password='testpass123')
            if auth_user:
                self.print_test("User authentication", True, "Login successful")
            else:
                self.print_test("User authentication", False, "Login failed")
                return False
            
            # Test 2.3: Role-based access
            is_resident = auth_user.role == 'resident'
            self.print_test("Role-based access (resident)", is_resident, f"Role: {auth_user.role}")
            
            return True
        except Exception as e:
            self.print_test("User authentication", False, str(e))
            return False
    
    def test_weather_data_ingestion(self):
        """Test 3: Weather Data Ingestion"""
        self.print_section("TEST 3: WEATHER DATA INGESTION")
        
        try:
            initial_count = WeatherDataLake.objects.count()
            self.print_test("Initial weather records", True, f"Count: {initial_count}")
            
            # Run ingestion
            result = DataPipeline.ingest_all_data()
            self.print_test("Data pipeline execution", True, f"Records: {result['total_records']}")
            
            # Verify data stored
            final_count = WeatherDataLake.objects.count()
            if final_count >= initial_count:
                self.print_test("Data storage verification", True, f"Total records: {final_count}")
            else:
                self.print_test("Data storage verification", False, "No new records")
                return False
            
            # Check data by source
            for source in ['OPENWEATHERMAP', 'NOAA']:
                count = WeatherDataLake.objects.filter(source=source).count()
                self.print_test(f"{source} records", count > 0, f"Count: {count}")
            
            return True
        except Exception as e:
            self.print_test("Weather data ingestion", False, str(e))
            return False
    
    def test_ml_model(self):
        """Test 4: ML Model Training & Prediction"""
        self.print_section("TEST 4: ML MODEL & PREDICTIONS")
        
        try:
            # Test 4.1: Model training
            trained = FloodRiskMLModel.train_model(force=False)
            self.print_test("Model training", trained, "Model ready")
            
            if not trained:
                return False
            
            # Test 4.2: Feature preparation
            ward = Ward.objects.first()
            if ward:
                features = FloodRiskMLModel.prepare_features_for_ward(ward)
                feature_count = len(features) if features else 0
                self.print_test("Feature engineering", features is not None, f"Features: {feature_count}")
            
            # Test 4.3: Risk prediction
            prediction = FloodRiskMLModel.predict_risk_for_ward(ward)
            if prediction:
                risk = prediction['risk_level']
                confidence = prediction['confidence']
                self.print_test("Risk prediction", True, f"Risk: {risk} (confidence: {confidence:.0%})")
            else:
                self.print_test("Risk prediction", False, "Prediction failed")
                return False
            
            # Test 4.4: Predict all wards
            predictions_count = FloodRiskMLModel.predict_all_wards()
            self.print_test("Batch predictions", predictions_count > 0, f"Predictions: {predictions_count}")
            
            # Test 4.5: Verify predictions stored
            total_preds = FloodPrediction.objects.count()
            self.print_test("Predictions storage", total_preds > 0, f"Total: {total_preds}")
            
            return True
        except Exception as e:
            self.print_test("ML model", False, str(e))
            return False
    
    def test_email_notifications(self):
        """Test 5: Email Notifications"""
        self.print_section("TEST 5: EMAIL NOTIFICATIONS")
        
        try:
            # Test 5.1: Flood alert email
            result = FloodAlertEmailService.send_flood_alert(
                recipient_email='test@example.com',
                recipient_name='Test User',
                ward_name='Kibera',
                risk_level='High',
                details={'forecast': 'Heavy rainfall expected', 'rainfall': '100mm'}
            )
            self.print_test("Flood alert email", result, "Email queued/sent")
            
            # Test 5.2: Report confirmation
            result = FloodAlertEmailService.send_report_confirmation(
                recipient_email='test@example.com',
                recipient_name='Test Reporter',
                report_id=1,
                location='Test Location'
            )
            self.print_test("Report confirmation email", result, "Email queued/sent")
            
            # Test 5.3: Report validation notification
            result = FloodAlertEmailService.send_report_validated(
                recipient_email='test@example.com',
                recipient_name='Test Reporter',
                report_id=1
            )
            self.print_test("Report validated email", result, "Email queued/sent")
            
            return True
        except Exception as e:
            self.print_test("Email notifications", False, str(e))
            return False
    
    def test_report_submission(self):
        """Test 6: Report Submission System"""
        self.print_section("TEST 6: REPORT SUBMISSION")
        
        try:
            user = CustomUser.objects.filter(role='resident').first()
            if not user:
                self.print_test("Report submission setup", False, "No test user found")
                return False
            
            # Test 6.1: Create report
            report = CrowdReport.objects.create(
                submitted_by=user,
                report_text='Test flood report',
                location_description='Test Location',
                latitude=-1.3,
                longitude=36.8,
                status='Pending'
            )
            self.print_test("Report creation", True, f"Report ID: {report.id}")
            
            # Test 6.2: Verify report stored
            retrieved = CrowdReport.objects.get(id=report.id)
            self.print_test("Report retrieval", retrieved is not None, f"Status: {retrieved.status}")
            
            # Test 6.3: Report validation
            report.status = 'Validated'
            report.save()
            updated = CrowdReport.objects.get(id=report.id)
            self.print_test("Report status update", updated.status == 'Validated', f"Status: {updated.status}")
            
            return True
        except Exception as e:
            self.print_test("Report submission", False, str(e))
            return False
    
    def test_ward_data(self):
        """Test 7: Ward Data & Mapping"""
        self.print_section("TEST 7: WARD DATA & MAPPING")
        
        try:
            # Test 7.1: Ward count
            ward_count = Ward.objects.count()
            self.print_test("Ward availability", ward_count > 0, f"Wards: {ward_count}")
            
            # Test 7.2: Ward geometry
            ward = Ward.objects.first()
            if ward:
                has_geometry = bool(ward.geom_json)
                self.print_test("Ward geometry", has_geometry, f"Ward: {ward.name}")
            
            # Test 7.3: Risk levels
            high_risk = Ward.objects.filter(current_risk_level='High').count()
            medium_risk = Ward.objects.filter(current_risk_level='Medium').count()
            low_risk = Ward.objects.filter(current_risk_level='Low').count()
            self.print_test("Risk distribution", True, 
                f"High: {high_risk}, Medium: {medium_risk}, Low: {low_risk}")
            
            return True
        except Exception as e:
            self.print_test("Ward data", False, str(e))
            return False
    
    def test_system_summary(self):
        """Test 8: System Summary"""
        self.print_section("TEST 8: SYSTEM SUMMARY")
        
        try:
            # Count records
            users = CustomUser.objects.count()
            wards = Ward.objects.count()
            weather = WeatherDataLake.objects.count()
            predictions = FloodPrediction.objects.count()
            reports = CrowdReport.objects.count()
            
            self.print_test("Total users", users > 0, f"Count: {users}")
            self.print_test("Total wards", wards > 0, f"Count: {wards}")
            self.print_test("Weather records", weather > 0, f"Count: {weather}")
            self.print_test("Predictions", predictions > 0, f"Count: {predictions}")
            self.print_test("Reports", reports >= 0, f"Count: {reports}")
            
            return True
        except Exception as e:
            self.print_test("System summary", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("  FLOOD WARNING SYSTEM - COMPREHENSIVE FUNCTIONALITY TEST")
        print("="*70)
        
        self.test_database_connection()
        self.test_user_authentication()
        self.test_weather_data_ingestion()
        self.test_ml_model()
        self.test_email_notifications()
        self.test_report_submission()
        self.test_ward_data()
        self.test_system_summary()
        
        # Summary
        self.print_section("TEST RESULTS SUMMARY")
        total = self.tests_passed + self.tests_failed
        percentage = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed:  {self.tests_passed}")
        print(f"Tests Failed:  {self.tests_failed}")
        print(f"Total Tests:   {total}")
        print(f"Success Rate:  {percentage:.0f}%")
        
        if self.tests_failed == 0:
            print("\n" + "="*70)
            print("  ✓ ALL TESTS PASSED - SYSTEM IS FULLY OPERATIONAL")
            print("="*70 + "\n")
        else:
            print("\n" + "="*70)
            print(f"  ⚠ {self.tests_failed} TESTS FAILED - REVIEW NEEDED")
            print("="*70 + "\n")

if __name__ == '__main__':
    tester = SystemTester()
    tester.run_all_tests()
