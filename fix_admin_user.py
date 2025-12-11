import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_warning_system.settings')
django.setup()

from core.models import CustomUser

print("\n" + "="*60)
print("  ADMIN USER VERIFICATION & FIX")
print("="*60 + "\n")

try:
    # Get or create admin user
    admin, created = CustomUser.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@floodwarning.ke',
            'role': 'authority',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    
    if created:
        admin.set_password('Admin@123456')
        admin.save()
        print("✓ Created new admin user")
    else:
        # Update existing admin to ensure correct permissions
        admin.role = 'authority'
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.save()
        print("✓ Updated existing admin user")
    
    print(f"\n  Username:     {admin.username}")
    print(f"  Email:        {admin.email}")
    print(f"  Role:         {admin.role}")
    print(f"  Is Staff:     {admin.is_staff}")
    print(f"  Is Superuser: {admin.is_superuser}")
    print(f"  Is Active:    {admin.is_active}")
    
    print("\n" + "="*60)
    print("  ✓ ADMIN USER READY")
    print("="*60)
    print("\n  Access URLs:")
    print("  - Dashboard:       http://localhost:8000/dashboard/")
    print("  - Admin Dashboard: http://localhost:8000/authority/dashboard/")
    print("  - Django Admin:    http://localhost:8000/admin/")
    print("\n  Login Credentials:")
    print("  - Username: admin")
    print("  - Password: Admin@123456")
    print()

except Exception as e:
    print(f"✗ Error: {e}")
