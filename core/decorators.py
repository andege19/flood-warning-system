from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

def authority_required(view_func):
    """
    Decorator that checks if the user has the 'authority' role.
    Must be used after @login_required decorator.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.role != 'authority':
            return HttpResponseForbidden(
                "You do not have permission to access this page."
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper