from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.views import redirect_to_login


def voter_required(view_func):
    """Restrict view to authenticated voters (session has voter_id, voter exists and is active)."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        voter_id = request.session.get("voter_id")
        if not voter_id:
            request.session["next_after_voter_login"] = request.get_full_path()
            return redirect("core:login")
        from core.models import Voter
        try:
            voter = Voter.objects.get(pk=voter_id, is_active=True)
        except Voter.DoesNotExist:
            request.session.flush()
            return redirect("core:login")
        request.voter = voter
        return view_func(request, *args, **kwargs)
    return _wrapped


def staff_required(view_func):
    """Restrict view to authenticated staff (admin) users."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url=reverse("core:admin_login"))
        if not request.user.is_staff:
            return redirect("core:login")
        return view_func(request, *args, **kwargs)
    return _wrapped
