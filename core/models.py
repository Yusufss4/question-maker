from django.db import models


class Voter(models.Model):
    """Normal user who logs in with EnterPass (4-char alphanumeric)."""
    full_name = models.CharField(max_length=255)
    enter_pass = models.CharField(max_length=4, unique=True, db_index=True)
    vote_weight = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class Survey(models.Model):
    """A single-question survey with multiple options (single-choice)."""
    question_text = models.TextField()
    end_date_time = models.DateTimeField(db_index=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-end_date_time"]

    def __str__(self):
        return self.question_text[:50]

    @property
    def is_closed(self):
        from django.utils import timezone
        return timezone.now() >= self.end_date_time


class Option(models.Model):
    """Selectable answer for a survey."""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="options")
    option_text = models.CharField(max_length=500)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.option_text


class Vote(models.Model):
    """A voter's selection of one option for a survey; weight recorded at vote time."""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="votes")
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name="votes")
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name="votes")
    recorded_weight = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["survey", "voter"]]
        ordering = ["survey", "voter"]

    def __str__(self):
        return f"{self.voter.full_name} -> {self.option.option_text}"
