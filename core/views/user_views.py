"""User-area views: active surveys, voting, results."""
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.db.models import Count, Sum
from core.decorators import voter_required
from core.models import Survey, Vote
from core.forms import VoteForm


@voter_required
@require_http_methods(["GET"])
def survey_list(request):
    """Single surveys page: active surveys with inline vote form, closed surveys with results preview."""
    now = timezone.now()
    voter = request.voter
    active_surveys = Survey.objects.filter(
        is_published=True,
        end_date_time__gt=now,
    ).order_by("end_date_time").prefetch_related("options")
    closed_surveys = Survey.objects.filter(
        is_published=True,
        end_date_time__lte=now,
    ).order_by("-end_date_time").prefetch_related("options")
    # For each active survey: (survey, existing_vote or None, form or None)
    active_with_forms = []
    for survey in active_surveys:
        existing = Vote.objects.filter(survey=survey, voter=voter).select_related("option").first()
        if existing:
            active_with_forms.append((survey, existing, None))
        else:
            active_with_forms.append((survey, None, VoteForm(survey)))
    # For each closed survey: option_stats (vote_count, %, weighted_total, %) for preview
    closed_with_preview = []
    for survey in closed_surveys:
        option_stats = survey.options.annotate(
            vote_count=Count("votes"),
            weighted_total=Sum("votes__recorded_weight"),
        ).order_by("id")
        total_votes = sum(o.vote_count for o in option_stats)
        total_weighted = sum(o.weighted_total or 0 for o in option_stats)
        for o in option_stats:
            o.vote_pct = (100 * o.vote_count / total_votes) if total_votes else 0
            o.weighted_pct = (100 * (o.weighted_total or 0) / total_weighted) if total_weighted else 0
        closed_with_preview.append((survey, list(option_stats)))
    return render(request, "user/survey_list.html", {
        "active_with_forms": active_with_forms,
        "closed_with_preview": closed_with_preview,
    })


@voter_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def survey_vote(request, pk):
    """Handle vote POST. GET redirects to survey list (voting is inline there)."""
    if request.method == "GET":
        return redirect("core:survey_list")
    survey = get_object_or_404(Survey, pk=pk)
    now = timezone.now()
    if now >= survey.end_date_time:
        return redirect("core:results_detail", pk=pk)
    if not survey.is_published:
        return redirect("core:survey_list")
    voter = request.voter
    if Vote.objects.filter(survey=survey, voter=voter).exists():
        return redirect("core:survey_list")
    form = VoteForm(survey, request.POST)
    if form.is_valid():
        option = form.cleaned_data["option"]
        if option.survey_id == survey.pk:
            with transaction.atomic():
                Vote.objects.create(
                    survey=survey,
                    voter=voter,
                    option=option,
                    recorded_weight=voter.vote_weight,
                )
    return redirect("core:survey_list")


@voter_required
@require_http_methods(["GET"])
def survey_detail(request, pk):
    """Redirect to vote page if open, else to results detail."""
    survey = get_object_or_404(Survey, pk=pk)
    if timezone.now() >= survey.end_date_time:
        return redirect("core:results_detail", pk=pk)
    return redirect("core:survey_vote", pk=pk)


@voter_required
@require_http_methods(["GET"])
def results_list(request):
    """Redirect to survey list (closed surveys are shown there)."""
    return redirect("core:survey_list")


@voter_required
@require_http_methods(["GET"])
def results_detail(request, pk):
    """Results for one survey: per-option totals and named voter list."""
    survey = get_object_or_404(Survey, pk=pk)
    if timezone.now() < survey.end_date_time:
        return redirect("core:survey_vote", pk=pk)
    votes = Vote.objects.filter(survey=survey).select_related("voter", "option")
    # Per-option: count, weighted total, and percentages
    from django.db.models import Count, Sum
    option_stats = survey.options.annotate(
        vote_count=Count("votes"),
        weighted_total=Sum("votes__recorded_weight"),
    ).order_by("id")
    total_votes = sum(o.vote_count for o in option_stats)
    total_weighted = sum(o.weighted_total or 0 for o in option_stats)
    for o in option_stats:
        o.vote_pct = (100 * o.vote_count / total_votes) if total_votes else 0
        o.weighted_pct = (100 * (o.weighted_total or 0) / total_weighted) if total_weighted else 0
    return render(request, "user/results_detail.html", {
        "survey": survey,
        "option_stats": option_stats,
        "votes": votes,
    })
