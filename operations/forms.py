from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from jobs.models import ManualVacancySubmission
from jobs.connectors.elempleo import validate_elempleo_vacancy_url


class ApplicantCreationForm(UserCreationForm):
    email = forms.EmailField(label="Correo electrónico", required=True)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")


class InvitationEmailForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico de la persona invitada")


class InvitationAcceptanceForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username",)


class ManualVacancySubmissionForm(forms.ModelForm):
    class Meta:
        model = ManualVacancySubmission
        fields = ("original_url",)
        widgets = {"original_url": forms.URLInput(attrs={"placeholder": "https://www.elempleo.com/co/ofertas-trabajo/...", "inputmode": "url"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["original_url"].label = "URL de la vacante"
        self.fields["original_url"].help_text = "Pega el enlace público de una vacante de El Empleo."

    def clean_original_url(self):
        url = self.cleaned_data["original_url"].strip()
        try:
            return validate_elempleo_vacancy_url(url)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc


