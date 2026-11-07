import json

from django import forms

from .models import Profile


class ProfileForm(forms.ModelForm):
    min_score = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=10,
        label="Descarte automático por puntaje",
        help_text=(
            "Las vacantes nuevas con un puntaje inferior a este valor pasarán automáticamente a Descartadas. "
            "Los cambios aplican solo a vacantes encontradas después de guardar; 0 desactiva el descarte por puntaje."
        ),
        widget=forms.HiddenInput(),
    )
    search_phrases = forms.CharField(
        required=False,
        label="Frases para buscar",
        help_text="Agrega los cargos o áreas que te interesan. La IA propondrá términos relacionados con tu hoja de vida.",
        widget=forms.Textarea(attrs={"rows": 3, "data-chip-editor": "search_phrases"}),
    )
    locations = forms.CharField(
        required=False,
        label="Ubicaciones",
        help_text="Agrega las ciudades o regiones donde aceptarías trabajar.",
        widget=forms.Textarea(attrs={"rows": 2, "data-chip-editor": "locations"}),
    )

    class Meta:
        model = Profile
        fields = ["search_phrases", "locations", "remote_ok", "min_score", "cv_file"]
        labels = {
            "remote_ok": "También me interesan vacantes remotas",
            "cv_file": "Hoja de vida (PDF o DOCX)",
        }
        help_texts = {
            "cv_file": "Sube una nueva versión si quieres actualizarla. Si lo dejas vacío, conservaremos la actual.",
        }
        widgets = {
            "cv_file": forms.FileInput(attrs={"accept": ".pdf,.docx"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("search_phrases", "locations"):
            value = self.initial.get(field_name, [])
            if isinstance(value, list):
                self.initial[field_name] = "\n".join(value)

    def clean_search_phrases(self):
        return self._clean_list_field(self.cleaned_data.get("search_phrases", ""), "frase", 100)

    def clean_min_score(self):
        if "min_score" not in self.data:
            return self.instance.min_score or 0
        return self.cleaned_data["min_score"]

    def clean_locations(self):
        return self._clean_list_field(self.cleaned_data.get("locations", ""), "ubicación", 120)

    @staticmethod
    def _clean_list_field(value, label, max_length):
        value = value.strip()
        if not value:
            return []
        if value.startswith("["):
            try:
                values = json.loads(value)
            except json.JSONDecodeError as exc:
                raise forms.ValidationError("La lista contiene un formato inválido.") from exc
            if not isinstance(values, list):
                raise forms.ValidationError("El valor debe ser una lista.")
        else:
            values = value.splitlines()
        result = []
        seen = set()
        for item in values:
            if not isinstance(item, str):
                raise forms.ValidationError(f"Cada {label} debe ser texto.")
            item = " ".join(item.split())
            if not item:
                continue
            if len(item) > max_length:
                raise forms.ValidationError(f"Cada {label} debe tener {max_length} caracteres o menos.")
            if item.casefold() not in seen:
                result.append(item)
                seen.add(item.casefold())
        return result

    def clean(self):
        cleaned_data = super().clean()
        uploaded_cv = cleaned_data.get("cv_file")
        if not uploaded_cv and not self.instance.cv_file:
            self.add_error("cv_file", "Carga tu hoja de vida para activar tu perfil.")
        if uploaded_cv and uploaded_cv.size > 10 * 1024 * 1024:
            self.add_error("cv_file", "El archivo debe pesar 10 MB o menos.")
        return cleaned_data
