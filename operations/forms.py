from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.core.mail import EmailMultiAlternatives
from django.template import loader

from jobs.models import ManualVacancySubmission
from jobs.connectors.elempleo import validate_elempleo_vacancy_url


class ApplicantCreationForm(UserCreationForm):
    email = forms.EmailField(label="Correo electrónico", required=True)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")


class StrictPasswordResetForm(PasswordResetForm):
    target_user = None

    def get_users(self, email):
        if (
            self.target_user
            and self.target_user.is_active
            and self.target_user.has_usable_password()
            and self.target_user.email.casefold() == email.casefold()
        ):
            return iter((self.target_user,))
        return iter(())

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email,
                  html_email_template_name=None):
        subject = "".join(loader.render_to_string(subject_template_name, context).splitlines())
        body = loader.render_to_string(email_template_name, context)
        message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name:
            message.attach_alternative(loader.render_to_string(html_email_template_name, context), "text/html")
        message.send(fail_silently=False)


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


