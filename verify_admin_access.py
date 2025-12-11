import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_warning_system.settings')
django.setup()

from core.models import CustomUser

print("\n" + "="*70)
print("  ADMIN ACCESS VERIFICATION")
print("="*70 + "\n")

try:
    admin = CustomUser.objects.get(username='admin')
    
    print(f"Username:     {admin.username}")
    print(f"Email:        {admin.email}")
    print(f"Role:         {admin.role}")
    print(f"Is Staff:     {admin.is_staff}")
    print(f"Is Superuser: {admin.is_superuser}")
    print(f"Is Active:    {admin.is_active}")
    
    print("\n" + "="*70)
    
    if admin.role == 'authority':
        print("  ✓ ADMIN HAS AUTHORITY ACCESS")
        print("  You can access: http://localhost:8000/authority/dashboard")
    else:
        print("  ✗ ADMIN DOES NOT HAVE AUTHORITY ROLE")
        print("  Run: python manage.py create_authority_user")
    
    print("="*70 + "\n")

except CustomUser.DoesNotExist:
    print("✗ Admin user not found")
    print("Run: python manage.py create_authority_user")
