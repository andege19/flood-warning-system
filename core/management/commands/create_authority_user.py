from django.core.management.base import BaseCommand
from core.models import CustomUser

class Command(BaseCommand):
    help = 'Create or update authority user account'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for authority account'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for authority account'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@floodwarning.ke',
            help='Email for authority account'
        )
    
    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        
        try:
            # Try to get existing user
            user = CustomUser.objects.get(username=username)
            
            # Update to authority role
            user.role = 'authority'
            user.is_staff = True
            user.is_superuser = True
            user.email = email
            user.set_password(password)
            user.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'✓ Updated existing user "{username}" to authority role'
            ))
        
        except CustomUser.DoesNotExist:
            # Create new authority user
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='authority',
                is_staff=True,
                is_superuser=True
            )
            
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created new authority user "{username}"'
            ))
        
        self.stdout.write(self.style.SUCCESS('\nAuthority User Details:'))
        self.stdout.write(f'  Username: {username}')
        self.stdout.write(f'  Password: {password}')
        self.stdout.write(f'  Email: {email}')
        self.stdout.write(f'  Role: {user.role}')
        self.stdout.write(f'  Is Staff: {user.is_staff}')
        self.stdout.write(f'  Is Superuser: {user.is_superuser}')
        self.stdout.write(self.style.SUCCESS('\n✓ You can now access the authority dashboard!'))
