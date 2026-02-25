"""User-area views: active surveys, voting, results."""
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from core.decorators import voter_required
from core.models import Survey, Vote
from core.forms import VoteForm


@voter_required
@require_http_methods(["GET"])
def survey_list(request):
    """List active (published, not closed) surveys."""
    now = timezone.now()
    surveys = Survey.objects.filter(
        is_published=True,
        end_date_time__gt=now,
    ).order_by("end_date_time").prefetch_related("options")
    return render(request, "user/survey_list.html", {"surveys": surveys})


@voter_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def survey_vote(request, pk):
    """Show vote form or submit vote. Redirect to results if survey is closed."""
    survey = get_object_or_404(Survey, pk=pk)
    now = timezone.now()
    if now >= survey.end_date_time:
        return redirect("core:results_detail", pk=pk)
    if not survey.is_published:
        return redirect("core:survey_list")
    voter = request.voter
    existing = Vote.objects.filter(survey=survey, voter=voter).first()
    if existing:
        return render(request, "user/vote.html", {"survey": survey, "already_voted": True, "existing_vote": existing})
    if request.method == "POST":
        form = VoteForm(survey, request.POST)
        if form.is_valid():
            option = form.cleaned_data["option"]
            if option.survey_id != survey.pk:
                form.add_error(None, "Invalid option for this survey.")
            else:
                with transaction.atomic():
                    Vote.objects.create(
                        survey=survey,
                        voter=voter,
                        option=option,
                        recorded_weight=voter.vote_weight,
                    )
                return redirect("core:survey_list")
    else:
        form = VoteForm(survey)
    return render(request, "user/vote.html", {"survey": survey, "form": form, "already_voted": False})


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
    """List closed surveys (results available)."""
    now = timezone.now()
    surveys = Survey.objects.filter(
        is_published=True,
        end_date_time__lte=now,
    ).order_by("-end_date_time")
    return render(request, "user/results_list.html", {"surveys": surveys})


@voter_required
@require_http_methods(["GET"])
def results_detail(request, pk):
    """Results for one survey: per-option totals and named voter list."""
    survey = get_object_or_404(Survey, pk=pk)
    if timezone.now() < survey.end_date_time:
        return redirect("core:survey_vote", pk=pk)
    votes = Vote.objects.filter(survey=survey).select_related("voter", "option")
    # Per-option: count and weighted total
    from django.db.models import Count, Sum
    option_stats = survey.options.annotate(
        vote_count=Count("votes"),
        weighted_total=Sum("votes__recorded_weight"),
    ).order_by("id")
    return render(request, "user/results_detail.html", {
        "survey": survey,
        "option_stats": option_stats,
        "votes": votes,
    })
