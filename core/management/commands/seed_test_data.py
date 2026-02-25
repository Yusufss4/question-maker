"""
Seed the database with test users, surveys (open/closed, published/unpublished), and votes.

Run from project root:
    python manage.py seed_test_data

Optional: clear existing data first (removes all Voters, Surveys, Options, Votes; does not touch admin users):
    python manage.py seed_test_data --clear
"""
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.crypto import get_random_string
from core.models import Voter, Survey, Option, Vote


def generate_enter_pass():
    """Generate a unique 4-char alphanumeric EnterPass."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(100):
        code = get_random_string(4, chars)
        if not Voter.objects.filter(enter_pass=code).exists():
            return code
    raise ValueError("Could not generate unique EnterPass")


class Command(BaseCommand):
    help = "Add test users, surveys (open/closed, published/unpublished), and votes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all Voters, Surveys, Options, and Votes before seeding (does not touch admin users).",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing voters, surveys, options, votes...")
            Vote.objects.all().delete()
            Option.objects.all().delete()
            Survey.objects.all().delete()
            Voter.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared."))

        now = timezone.now()

        # ---- Users ----
        user_data = [
            ("Alice Smith", 1.0),
            ("Bob Jones", 1.0),
            ("Carol White", 2.0),
            ("Dave Brown", 1.5),
            ("Eve Davis", 1.0),
            ("Frank Miller", 3.0),
            ("Grace Lee", 1.0),
            ("Henry Wilson", 2.0),
            ("Ivy Taylor", 1.0),
            ("Jack Clark", 1.5),
        ]
        voters = []
        for full_name, weight in user_data:
            voter, created = Voter.objects.get_or_create(
                full_name=full_name,
                defaults={"enter_pass": generate_enter_pass(), "vote_weight": weight, "is_active": True},
            )
            if created:
                voters.append(voter)
                self.stdout.write(f"  Created voter: {full_name} (EnterPass: {voter.enter_pass}, weight: {weight})")
            else:
                voters.append(voter)

        if not voters:
            self.stdout.write("No new voters created (all already exist). Using existing voters for surveys.")
            voters = list(Voter.objects.filter(is_active=True)[:15])

        # ---- Surveys: mix of open/closed, published/unpublished ----
        surveys_config = [
            # (question, end_date_offset_days, is_published, options_list)
            ("What is your preferred meeting time?", 5, True, ["Morning (9–12)", "Afternoon (12–17)", "Evening (17–21)"]),
            ("Should we have a team lunch this week?", 2, True, ["Yes", "No", "Maybe"]),
            ("Which project should we prioritize?", -1, True, ["Project A", "Project B", "Project C"]),  # closed
            ("Rate the last sprint.", -3, True, ["Poor", "Fair", "Good", "Excellent"]),  # closed
            ("Preferred remote work days?", 7, True, ["Mon–Fri", "Flexible", "Office only"]),
            ("Draft: Internal feedback (unpublished)", 10, False, ["Option 1", "Option 2"]),  # not published
            ("Old closed survey (no recent votes).", -30, True, ["Yes", "No"]),  # closed long ago
            ("Quick poll: Coffee or tea?", 1, True, ["Coffee", "Tea", "Neither"]),
        ]

        created_surveys = []
        for question, end_days, is_pub, option_texts in surveys_config:
            end_dt = now + timedelta(days=end_days)
            survey, created = Survey.objects.get_or_create(
                question_text=question,
                defaults={"end_date_time": end_dt, "is_published": is_pub},
            )
            if created:
                for text in option_texts:
                    Option.objects.create(survey=survey, option_text=text)
                created_surveys.append(survey)
                status = "closed" if end_dt <= now else "open"
                short_q = question[:50] + ("..." if len(question) > 50 else "")
                self.stdout.write(f"  Created survey: \"{short_q}\" ({status}, published={is_pub})")
            else:
                created_surveys.append(survey)

        # ---- Votes: add some votes to surveys that have options ----
        surveys_with_options = list(Survey.objects.prefetch_related("options").filter(options__isnull=False).distinct())
        vote_count = 0
        for survey in surveys_with_options:
            options = list(survey.options.all())
            if not options or not voters:
                continue
            # Pick a random subset of voters to have voted
            n_voters = random.randint(1, min(len(voters), 6))
            chosen_voters = random.sample(voters, n_voters)
            for v in chosen_voters:
                if Vote.objects.filter(survey=survey, voter=v).exists():
                    continue
                opt = random.choice(options)
                Vote.objects.create(
                    survey=survey,
                    voter=v,
                    option=opt,
                    recorded_weight=v.vote_weight,
                )
                vote_count += 1
        if vote_count:
            self.stdout.write(f"  Created {vote_count} vote(s).")

        self.stdout.write(self.style.SUCCESS("Done. Use admin or user login to view."))
        if voters:
            self.stdout.write("Sample voter EnterPass codes (if just created): " + ", ".join(v.enter_pass for v in voters[:5]))
