import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from core.models import Voter, Survey, Option, Vote


# ----- EnterPass login -----
class EnterPassLoginForm(forms.Form):
    enter_pass = forms.CharField(
        max_length=4,
        min_length=4,
        strip=True,
        widget=forms.TextInput(attrs={"placeholder": "Enter 4-character code", "autocomplete": "off", "maxlength": "4"}),
        label="Enter your code",
    )

    def clean_enter_pass(self):
        value = self.cleaned_data.get("enter_pass", "").strip().upper()
        if len(value) != 4:
            raise forms.ValidationError("Code must be exactly 4 characters.")
        if not re.match(r"^[A-Z0-9]{4}$", value):
            raise forms.ValidationError("Code must contain only letters and numbers.")
        try:
            voter = Voter.objects.get(enter_pass=value, is_active=True)
        except Voter.DoesNotExist:
            raise forms.ValidationError("Invalid code.")
        self.voter = voter
        return value


# ----- Admin login uses Django's AuthenticationForm -----
class AdminLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if hasattr(field.widget, "attrs"):
                field.widget.attrs.setdefault("class", "form-control")


# ----- Survey (admin) -----
class SurveyForm(forms.ModelForm):
    end_date_time = forms.SplitDateTimeField(
        widget=forms.SplitDateTimeWidget(
            date_attrs={"type": "date", "class": "form-control"},
            time_attrs={"type": "time", "class": "form-control"},
        ),
        label="End date/time",
    )

    class Meta:
        model = Survey
        fields = ["question_text", "end_date_time", "is_published"]
        widgets = {
            "question_text": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class OptionFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        options = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE")]
        if len(options) < 2:
            raise forms.ValidationError("At least 2 options are required.")


OptionFormSetFactory = forms.inlineformset_factory(
    Survey,
    Option,
    fields=("option_text",),
    extra=5,
    min_num=2,
    validate_min=True,
    formset=OptionFormSet,
    widgets={"option_text": forms.TextInput(attrs={"class": "form-control", "placeholder": "Option text"})},
)


# ----- Vote (user) -----
class VoteForm(forms.Form):
    option = forms.ModelChoiceField(
        queryset=Option.objects.none(),
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        empty_label=None,
    )

    def __init__(self, survey, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["option"].queryset = survey.options.all()


# ----- Add user (admin) -----
class VoterCreateForm(forms.ModelForm):
    class Meta:
        model = Voter
        fields = ["full_name", "vote_weight"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "vote_weight": forms.NumberInput(attrs={"step": "0.01", "min": "0", "class": "form-control"}),
        }


# ----- Vote reset (admin) -----
class VoteResetForm(forms.Form):
    survey = forms.ModelChoiceField(queryset=Survey.objects.all().order_by("-end_date_time"), label="Survey", widget=forms.Select(attrs={"class": "form-select"}))
    voter = forms.ModelChoiceField(queryset=Voter.objects.filter(is_active=True).order_by("full_name"), label="User", widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: filter voters by survey (only those who voted) after survey is selected via JS or second step
        pass

    def clean(self):
        data = super().clean()
        survey = data.get("survey")
        voter = data.get("voter")
        if survey and voter:
            if not Vote.objects.filter(survey=survey, voter=voter).exists():
                raise forms.ValidationError("This user has not voted on the selected survey.")
        return data
