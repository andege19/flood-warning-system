from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError, JsonResponse, HttpResponse
from .forms import CustomUserCreationForm
from .models import CrowdReport, Ward, HistoricalFloodEvent, FloodHistoricalData, SatelliteFloodData, ClimatePatternData
import json
import logging
from .decorators import authority_required
from django.views.decorators.http import require_POST
from core.services.email_service import FloodAlertEmailService
from django.db.models import Sum, Avg
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# --- Home Page View ---
def home_view(request):
    return render(request, "core/home.html")

# --- Signup View ---
def signup_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'resident' 
            user.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = CustomUserCreationForm()
    return render(request, "core/signup.html", {"form": form})

# --- Login View ---
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("dashboard")
    else:
        form = AuthenticationForm()
    return render(request, "core/login.html", {"form": form})

# --- Logout View ---
def logout_view(request):
    logout(request)
    return redirect("home")

def is_authority(user):
    """Strict check: user must be authenticated AND have authority role"""
    if not user.is_authenticated:
        return False
    return user.role == 'authority'

# --- Dashboard View (Protected) ---
@login_required
def dashboard_view(request):
    """
    Main dashboard - shows dashboard choice for ALL users.
    Authority users see admin stats plus access to both dashboards.
    Regular users see access to map, reports, and flood history.
    """
    pending_reports = CrowdReport.objects.filter(status='Pending').count()
    validated_reports = CrowdReport.objects.filter(status='Validated').count()
    rejected_reports = CrowdReport.objects.filter(status='Rejected').count()
    total_reports = CrowdReport.objects.count()
    
    context = {
        'pending_reports': pending_reports,
        'validated_reports': validated_reports,
        'rejected_reports': rejected_reports,
        'total_reports': total_reports,
    }
    
    return render(request, "core/dashboard_choice.html", context)

@login_required
def map_view(request):
    """Display map with filter - available to all authenticated users"""
    return render(request, "core/map.html")

@login_required(login_url='login')
def submit_report_page_view(request):
    """Display the flood report submission page"""
    return render(request, 'core/submit_report.html')

@login_required
def submit_report_view(request):
    """Handle flood report submission with automatic geolocation"""
    if request.method == "POST":
        try:
            location_desc = request.POST.get('location_description', '').strip()
            report_text = request.POST.get('report_text', '').strip()
            lat_str = request.POST.get('latitude', '').strip()
            lon_str = request.POST.get('longitude', '').strip()
            photo = request.FILES.get('photos')

            # Validate required fields
            if not location_desc:
                return HttpResponse('Location description is required', status=400)
            if not report_text:
                return HttpResponse('Report description is required', status=400)
            if not lat_str or not lon_str:
                return HttpResponse('Location data is required. Please allow geolocation.', status=400)

            # Parse coordinates
            try:
                latitude = float(lat_str)
                longitude = float(lon_str)
            except ValueError:
                return HttpResponse('Invalid location data', status=400)

            # Validate coordinates are within reasonable bounds (Nairobi area)
            if not (-1.5 < latitude < -0.8 and 36.5 < longitude < 37.2):
                return HttpResponse('Location appears to be outside Nairobi. Please verify your location.', status=400)

            # Validate file size
            if photo and photo.size > 5 * 1024 * 1024:
                return HttpResponse('File size exceeds 5MB limit', status=400)

            # Create report
            report = CrowdReport.objects.create(
                submitted_by=request.user,
                report_text=report_text,
                location_description=location_desc,
                latitude=latitude,
                longitude=longitude,
                photos=photo,
                status='Pending'
            )

            # Send confirmation email to user
            if request.user.email:
                FloodAlertEmailService.send_report_confirmation(
                    recipient_email=request.user.email,
                    recipient_name=request.user.username,
                    report_id=report.id,
                    location=location_desc
                )
                logger.info(f"Confirmation email sent to {request.user.email}")

            # Notify all authorities about new report
            FloodAlertEmailService.notify_authorities_new_report(report)
            logger.info(f"Authority notifications sent for report #{report.id}")

            logger.info(f"Report {report.id} created successfully with geolocation data")
            return HttpResponse(status=201)

        except Exception as e:
            logger.error(f"Error submitting report: {e}")
            return HttpResponse(f'Error: {str(e)}', status=400)

    return HttpResponse(status=405)

# --- Authority Dashboard View (Strictly Protected) ---
@login_required(login_url='login')
def authority_dashboard_view(request):
    """Admin dashboard with report management and notes"""
    
    if not request.user.role == 'authority':
        return render(request, 'core/forbidden.html', {
            'message': 'You do not have permission to access this dashboard.'
        }, status=403)
    
    pending_reports = CrowdReport.objects.filter(status='Pending').order_by('-created_at')
    recent_reports = CrowdReport.objects.all().order_by('-created_at')[:15]
    
    total_reports = CrowdReport.objects.count()
    validated_reports = CrowdReport.objects.filter(status='Validated').count()
    rejected_reports = CrowdReport.objects.filter(status='Rejected').count()
    pending_count = CrowdReport.objects.filter(status='Pending').count()
    
    # Handle form actions
    if request.method == 'POST':
        action = request.POST.get('action')
        report_id = request.POST.get('report_id')
        admin_notes = request.POST.get('admin_notes', '').strip()
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        
        try:
            report = CrowdReport.objects.get(id=report_id)
            
            if action == 'validate':
                report.status = 'Validated'
                report.save()
                
                # Create action record
                from core.models import ReportAction
                ReportAction.objects.create(
                    report=report,
                    action='validated',
                    admin=request.user,
                    notes=admin_notes
                )
                
                # Send validation email with notes
                if report.submitted_by.email:
                    FloodAlertEmailService.send_report_validated(
                        recipient_email=report.submitted_by.email,
                        recipient_name=report.submitted_by.username,
                        report_id=report.id,
                        admin_notes=admin_notes
                    )
                    logger.info(f"Validation email sent to {report.submitted_by.email} for report #{report_id}")
                
            elif action == 'reject':
                report.status = 'Rejected'
                report.save()
                
                # Create action record
                from core.models import ReportAction
                ReportAction.objects.create(
                    report=report,
                    action='rejected',
                    admin=request.user,
                    notes=rejection_reason
                )
                
                # Send rejection email with reason
                if report.submitted_by.email:
                    FloodAlertEmailService.send_report_rejected(
                        recipient_email=report.submitted_by.email,
                        recipient_name=report.submitted_by.username,
                        report_id=report.id,
                        reason=rejection_reason
                    )
                    logger.info(f"Rejection email sent to {report.submitted_by.email} for report #{report_id}")
        
        except CrowdReport.DoesNotExist:
            logger.warning(f"Report #{report_id} not found")
        
        return redirect('authority-dashboard')
    
    context = {
        'pending_reports': pending_reports,
        'recent_reports': recent_reports,
        'total_reports': total_reports,
        'validated_reports': validated_reports,
        'rejected_reports': rejected_reports,
        'pending_count': pending_count,
    }
    
    return render(request, "core/authority_dashboard.html", context)

@login_required
@authority_required
@require_POST
def validate_report_view(request, report_id):
    """Validate a report and send notification"""
    try:
        report = CrowdReport.objects.get(id=report_id)
        report.status = 'Validated'
        report.save()
        
        FloodAlertEmailService.send_report_validated(
            recipient_email=report.submitted_by.email,
            recipient_name=report.submitted_by.username,
            report_id=report.id
        )
        
        logger.info(f"Report {report_id} validated")
        return redirect('authority-dashboard')
    
    except CrowdReport.DoesNotExist:
        return HttpResponseNotFound()
    except Exception as e:
        logger.error(f"Error validating report: {e}")
        return HttpResponseServerError()

@login_required
@authority_required
@require_POST
def reject_report_view(request, report_id):
    """Reject a report"""
    report = get_object_or_404(CrowdReport, id=report_id)
    report.status = 'Rejected'
    report.save()
    return redirect('authority-dashboard')

# --- API Views ---

@login_required
def ward_data_view(request):
    """API for ward data - returns GeoJSON"""
    try:
        wards = Ward.objects.only('id', 'name', 'geom_json', 'current_risk_level')
        
        features = []
        for ward in wards:
            try:
                ward_geometry = json.loads(ward.geom_json)
                features.append({
                    "type": "Feature",
                    "geometry": ward_geometry,
                    "properties": {
                        "id": ward.id,
                        "name": ward.name,
                        "current_risk_level": ward.current_risk_level 
                    }
                })
            except json.JSONDecodeError:
                logger.error(f"Invalid GeoJSON for ward: {ward.name}")
                continue

        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }
        
        response = JsonResponse(feature_collection)
        response['Cache-Control'] = 'public, max-age=300'
        return response
        
    except Exception as e:
        logger.error(f"Error in ward_data_view: {str(e)}")
        return JsonResponse({'error': 'Failed to load ward data'}, status=500)

@login_required
def submit_report_view(request):
    """Handle flood report submission with automatic geolocation"""
    if request.method == "POST":
        try:
            location_desc = request.POST.get('location_description', '').strip()
            report_text = request.POST.get('report_text', '').strip()
            lat_str = request.POST.get('latitude', '').strip()
            lon_str = request.POST.get('longitude', '').strip()
            photo = request.FILES.get('photos')

            # Validate required fields
            if not location_desc:
                return HttpResponse('Location description is required', status=400)
            if not report_text:
                return HttpResponse('Report description is required', status=400)
            if not lat_str or not lon_str:
                return HttpResponse('Location data is required. Please allow geolocation.', status=400)

            # Parse coordinates
            try:
                latitude = float(lat_str)
                longitude = float(lon_str)
            except ValueError:
                return HttpResponse('Invalid location data', status=400)

            # Validate coordinates are within reasonable bounds (Nairobi area)
            if not (-1.5 < latitude < -0.8 and 36.5 < longitude < 37.2):
                return HttpResponse('Location appears to be outside Nairobi. Please verify your location.', status=400)

            # Validate file size
            if photo and photo.size > 5 * 1024 * 1024:
                return HttpResponse('File size exceeds 5MB limit', status=400)

            # Create report
            report = CrowdReport.objects.create(
                submitted_by=request.user,
                report_text=report_text,
                location_description=location_desc,
                latitude=latitude,
                longitude=longitude,
                photos=photo,
                status='Pending'
            )

            # Send confirmation email to user
            if request.user.email:
                FloodAlertEmailService.send_report_confirmation(
                    recipient_email=request.user.email,
                    recipient_name=request.user.username,
                    report_id=report.id,
                    location=location_desc
                )
                logger.info(f"Confirmation email sent to {request.user.email}")

            # Notify all authorities about new report
            FloodAlertEmailService.notify_authorities_new_report(report)
            logger.info(f"Authority notifications sent for report #{report.id}")

            logger.info(f"Report {report.id} created successfully with geolocation data")
            return HttpResponse(status=201)

        except Exception as e:
            logger.error(f"Error submitting report: {e}")
            return HttpResponse(f'Error: {str(e)}', status=400)

    return HttpResponse(status=405)

@login_required
def report_status_view(request, report_id):
    """Display the status of a submitted flood report"""
    try:
        report = CrowdReport.objects.get(id=report_id)
        
        if request.user != report.submitted_by and request.user.role != 'authority':
            return HttpResponseForbidden()
        
        context = {
            'report': report,
            'status_color': {
                'Pending': '#ff9800',
                'Validated': '#28a745',
                'Rejected': '#dc3545',
            }.get(report.status, '#6c757d')
        }
        
        return render(request, 'core/report_status.html', context)
    
    except CrowdReport.DoesNotExist:
        return HttpResponseNotFound()
    except Exception as e:
        logger.error(f"Error retrieving report status: {e}")
        return HttpResponseServerError()

@login_required
def flood_information_view(request):
    """Flood information page with historical data"""
    try:
        risk_filter = request.GET.get('risk', 'all')
        year_filter = request.GET.get('year', 'all')
        ward_filter = request.GET.get('ward', 'all')
        
        events = HistoricalFloodEvent.objects.all()
        
        if risk_filter != 'all':
            events = events.filter(risk_level=risk_filter)
        
        if year_filter != 'all':
            try:
                events = events.filter(date_occurred__year=int(year_filter))
            except (ValueError, TypeError):
                pass
        
        if ward_filter != 'all':
            try:
                events = events.filter(affected_wards__id=int(ward_filter))
            except (ValueError, TypeError):
                pass
        
        events = events.distinct().order_by('-date_occurred')
        
        all_events = HistoricalFloodEvent.objects.all()
        stats = {
            'total_events': all_events.count(),
            'total_casualties': all_events.aggregate(total=Sum('estimated_casualties'))['total'] or 0,
            'total_displaced': all_events.aggregate(total=Sum('estimated_displaced'))['total'] or 0,
            'total_damage': all_events.aggregate(total=Sum('estimated_damage_value'))['total'] or 0,
            'high_risk_events': all_events.filter(risk_level='High').count(),
        }
        
        ward_data = FloodHistoricalData.objects.select_related('ward').order_by('-flood_risk_score')[:10]
        
        context = {
            'events': events,
            'stats': stats,
            'ward_data': ward_data,
            'years': range(2015, 2026),
            'wards': Ward.objects.all().order_by('name'),
            'risk_levels': ['Low', 'Medium', 'High'],
        }
        
        return render(request, 'core/flood_information.html', context)
    
    except Exception as e:
        logger.error(f"Error in flood_information_view: {str(e)}")
        return render(request, 'core/flood_information.html', {
            'error': 'Error loading data',
            'stats': {'total_events': 0, 'total_casualties': 0, 'total_displaced': 0, 'total_damage': 0, 'high_risk_events': 0},
            'events': [],
            'ward_data': [],
            'years': range(2015, 2026),
            'wards': Ward.objects.all(),
        })

@login_required
def historical_event_detail_view(request, event_id):
    """Detailed view for a specific historical flood event"""
    try:
        event = HistoricalFloodEvent.objects.get(id=event_id)
        
        satellite_data = SatelliteFloodData.objects.filter(
            historical_event=event
        ).order_by('capture_date')
        
        affected_wards = event.affected_wards.all()
        
        context = {
            'event': event,
            'affected_wards': affected_wards,
            'satellite_data': satellite_data,
        }
        
        return render(request, 'core/historical_event_detail.html', context)
    
    except HistoricalFloodEvent.DoesNotExist:
        return render(request, 'core/not_found.html', {'message': 'Event not found'})

@login_required
def ward_flood_history_view(request, ward_id):
    """Flood history for a specific ward"""
    try:
        ward = Ward.objects.get(id=ward_id)
        
        events = HistoricalFloodEvent.objects.filter(
            affected_wards=ward
        ).order_by('-date_occurred').distinct()
        
        historical_data = FloodHistoricalData.objects.filter(
            ward=ward
        ).order_by('-year')
        
        climate_patterns = ClimatePatternData.objects.filter(
            ward=ward
        ).order_by('-year', 'month')
        
        context = {
            'ward': ward,
            'events': events,
            'historical_data': historical_data,
            'climate_patterns': climate_patterns,
        }
        
        return render(request, 'core/ward_flood_history.html', context)
    
    except Ward.DoesNotExist:
        return render(request, 'core/not_found.html', {'message': 'Ward not found'})

@login_required
def historical_flood_data_api(request):
    """API endpoint for historical flood data"""
    try:
        data = {}
        
        wards = Ward.objects.all()
        
        for ward in wards:
            hist_data = FloodHistoricalData.objects.filter(ward=ward).order_by('-year').first()
            flood_count = HistoricalFloodEvent.objects.filter(affected_wards=ward).count()
            probability = min((flood_count / 10) * 100, 100) if flood_count else 0
            
            risk_level = ward.current_risk_level
            if risk_level == 'High':
                probability = max(probability, 70)
            elif risk_level == 'Medium':
                probability = max(probability, 40)
            
            data[ward.id] = {
                'ward_name': ward.name,
                'probability': round(probability, 1),
                'flood_count': flood_count,
                'avg_rainfall': round(hist_data.avg_rainfall_mm, 1) if hist_data else 0,
                'vulnerability': round(hist_data.vulnerability_index, 1) if hist_data else 0,
                'risk_score': round(hist_data.flood_risk_score, 1) if hist_data else 0,
            }
        
        return JsonResponse(data)
    
    except Exception as e:
        logger.error(f"Error in historical_flood_data_api: {str(e)}")
        return JsonResponse({}, status=500)