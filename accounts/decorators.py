from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
from functools import wraps

from .models import UserProfile

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            try:
                profile = request.user.profile
            except (AttributeError, ObjectDoesNotExist):
                profile, _ = UserProfile.objects.get_or_create(
                    user=request.user,
                    defaults={'role': 'customer'},
                )

            user_role = profile.role
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                if user_role == 'admin':
                    return redirect('admin_dashboard')
                elif user_role == 'staff':
                    return redirect('staff_dashboard')
                elif user_role == 'rider':
                    return redirect('rider_dashboard')
                else:
                    return redirect('customer_dashboard')
        return _wrapped_view
    return decorator

def admin_required(view_func):
    return role_required(['admin'])(view_func)

def staff_required(view_func):
    return role_required(['admin', 'staff'])(view_func)

def rider_required(view_func):
    return role_required(['admin', 'staff', 'rider'])(view_func)

def customer_required(view_func):
    return role_required(['customer'])(view_func)