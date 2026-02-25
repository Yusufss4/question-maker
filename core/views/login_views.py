from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from core.forms import EnterPassLoginForm, AdminLoginForm


@require_http_methods(["GET", "POST"])
@csrf_protect
def login(request):
    """Public login: EnterPass for voters. GET shows form; POST validates and sets session."""
    if request.method == "POST":
        form = EnterPassLoginForm(request.POST)
        if form.is_valid():
            voter = form.voter
            request.session["voter_id"] = voter.pk
            request.session["voter_full_name"] = voter.full_name
            next_url = request.session.pop("next_after_voter_login", None) or "core:survey_list"
            return redirect(next_url)
    else:
        form = EnterPassLoginForm()
    return render(request, "login.html", {"form": form})


def voter_logout(request):
    """Clear voter session and redirect to login."""
    request.session.pop("voter_id", None)
    request.session.pop("voter_full_name", None)
    return redirect("core:login")


class AdminLoginView(LoginView):
    """Admin login: username + password. Restrict to staff users."""
    template_name = "admin/login.html"
    redirect_authenticated_url = "core:admin_dashboard"
    authentication_form = AdminLoginForm

    def get_success_url(self):
        from django.urls import reverse
        return reverse("core:admin_dashboard")

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_staff:
            from django.contrib import messages
            from django.contrib.auth import logout
            logout(self.request)
            messages.error(self.request, "Access denied. Staff only.")
            return redirect("core:admin_login")
        return super().form_valid(form)
