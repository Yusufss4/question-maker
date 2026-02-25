"""Admin views: dashboard, survey CRUD, user CRUD, export, vote reset."""
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from core.decorators import staff_required
from core.models import Voter, Survey, Option, Vote
from core.forms import SurveyForm, OptionFormSetFactory, VoterCreateForm, VoteResetForm
import openpyxl
from django.utils.crypto import get_random_string


def _generate_enter_pass():
    """Generate a unique 4-char alphanumeric EnterPass."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # avoid ambiguous 0/O, 1/I
    for _ in range(100):
        code = get_random_string(4, chars)
        if not Voter.objects.filter(enter_pass=code).exists():
            return code
    raise ValueError("Could not generate unique EnterPass")


# ----- Dashboard -----
@staff_required
@require_http_methods(["GET"])
def admin_dashboard(request):
    return render(request, "admin/dashboard.html")


# ----- Surveys -----
@staff_required
@require_http_methods(["GET"])
def admin_survey_list(request):
    surveys = Survey.objects.all().order_by("-created_at").prefetch_related("options")
    return render(request, "admin/survey_list.html", {"surveys": surveys})


@staff_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def admin_survey_create(request):
    form = SurveyForm(request.POST or None)
    formset = OptionFormSetFactory(request.POST or None, instance=Survey())
    if request.method == "POST":
        if form.is_valid():
            survey = form.save()
            formset = OptionFormSetFactory(request.POST, instance=survey)
            if formset.is_valid():
                formset.save()
                messages.success(request, "Survey created.")
                return redirect("core:admin_survey_list")
            survey.delete()
        else:
            formset = OptionFormSetFactory(request.POST, instance=Survey())
    return render(request, "admin/survey_form.html", {"form": form, "formset": formset, "survey": None})


@staff_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def admin_survey_edit(request, pk):
    survey = get_object_or_404(Survey, pk=pk)
    if timezone.now() >= survey.end_date_time:
        messages.error(request, "Cannot edit a closed survey.")
        return redirect("core:admin_survey_list")
    form = SurveyForm(request.POST or None, instance=survey)
    has_votes = survey.votes.exists()
    formset = OptionFormSetFactory(request.POST or None, instance=survey)
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            form.save()
            formset.save()
        messages.success(request, "Survey updated.")
        return redirect("core:admin_survey_list")
    return render(request, "admin/survey_form.html", {
        "form": form, "formset": formset, "survey": survey, "has_votes": has_votes,
    })


@staff_required
@require_http_methods(["POST"])
@csrf_protect
def admin_survey_toggle_publish(request, pk):
    survey = get_object_or_404(Survey, pk=pk)
    survey.is_published = not survey.is_published
    survey.save(update_fields=["is_published"])
    status = "published" if survey.is_published else "unpublished"
    messages.success(request, f"Survey {status}.")
    return redirect("core:admin_survey_list")


# ----- Users -----
@staff_required
@require_http_methods(["GET"])
def admin_user_list(request):
    users = Voter.objects.all().order_by("full_name")
    return render(request, "admin/user_list.html", {"users": users})


@staff_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def admin_user_create(request):
    form = VoterCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            voter = form.save(commit=False)
            voter.enter_pass = _generate_enter_pass()
            voter.save()
        messages.success(request, f"User created. EnterPass: {voter.enter_pass}")
        return redirect("core:admin_user_list")
    return render(request, "admin/user_form.html", {"form": form})


@staff_required
@require_http_methods(["POST"])
@csrf_protect
def admin_user_deactivate(request, pk):
    voter = get_object_or_404(Voter, pk=pk)
    voter.is_active = False
    voter.save(update_fields=["is_active"])
    messages.success(request, f"User {voter.full_name} deactivated.")
    return redirect("core:admin_user_list")


@staff_required
@require_http_methods(["POST"])
@csrf_protect
def admin_user_activate(request, pk):
    voter = get_object_or_404(Voter, pk=pk)
    voter.is_active = True
    voter.save(update_fields=["is_active"])
    messages.success(request, f"User {voter.full_name} activated.")
    return redirect("core:admin_user_list")


@staff_required
@require_http_methods(["POST"])
@csrf_protect
def admin_user_delete(request, pk):
    voter = get_object_or_404(Voter, pk=pk)
    name = voter.full_name
    voter.delete()
    messages.success(request, f"User {name} deleted.")
    return redirect("core:admin_user_list")


@staff_required
@require_http_methods(["GET"])
def admin_user_export(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Users"
    ws.append(["Full Name", "EnterPass", "Vote Weight", "Status"])
    for v in Voter.objects.all().order_by("full_name"):
        ws.append([v.full_name, v.enter_pass, float(v.vote_weight), "Active" if v.is_active else "Inactive"])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="users.xlsx"'
    return response


# ----- Vote reset -----
@staff_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def admin_vote_reset(request):
    form = VoteResetForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        survey = form.cleaned_data["survey"]
        voter = form.cleaned_data["voter"]
        deleted, _ = Vote.objects.filter(survey=survey, voter=voter).delete()
        if deleted:
            messages.success(request, f"Vote reset for {voter.full_name} on this survey.")
        return redirect("core:admin_vote_reset")
    return render(request, "admin/vote_reset.html", {"form": form})
