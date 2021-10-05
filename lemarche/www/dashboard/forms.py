from django import forms

from lemarche.siaes.models import Siae
from lemarche.users.models import User


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Mandatory fields.
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True

        # Disabled fields
        self.fields["email"].disabled = True


class SiaeSearchBySiretForm(forms.Form):
    siret = forms.CharField(
        label="Entrez le numéro SIRET ou SIREN de votre structure",
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=True,
    )

    def clean_siret(self):
        siret = self.cleaned_data["siret"]
        if siret:
            # strip spaces (beginning, inbetween, end)
            siret = siret.replace(" ", "")
            # siret/siren validation
            if len(siret) < 9:
                msg = "Le longueur du numéro doit être supérieure ou égale à 9 caractères."
                raise forms.ValidationError(msg)
            if len(siret) > 14:
                msg = "Le longueur du numéro ne peut pas dépasser 14 caractères."
                raise forms.ValidationError(msg)
            if not siret.isdigit():
                msg = "Le numéro ne doit être composé que de chiffres."
                raise forms.ValidationError(msg)
        return siret

    def filter_queryset(self):
        qs = Siae.objects.prefetch_related("users")

        if not hasattr(self, "cleaned_data"):
            self.full_clean()

        siret = self.cleaned_data.get("siret", None)
        if siret:
            qs = qs.filter(siret__startswith=siret)
        else:
            # show results only if there is a valid siret provided
            qs = qs.none()

        return qs


class SiaeAdoptConfirmForm(forms.ModelForm):
    class Meta:
        model = Siae
        fields = []


class SiaeEditForm(forms.ModelForm):
    kind = forms.CharField()
    department = forms.CharField()
    region = forms.CharField()
    presta_type = forms.MultipleChoiceField(
        label=Siae._meta.get_field("presta_type").verbose_name,
        choices=Siae.PRESTA_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    is_cocontracting = forms.BooleanField(
        label=Siae._meta.get_field("is_cocontracting").verbose_name,
        widget=forms.RadioSelect(choices=[(True, "Oui"), (False, "Non")]),
    )

    class Meta:
        model = Siae
        fields = [
            "name",
            "brand",
            "siret",
            "kind",
            "city",
            "post_code",
            "department",
            "region",
            "website",
            "description",
            "presta_type",
            "is_cocontracting",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Disabled fields
        for field in Siae.READONLY_FIELDS_FROM_C1:
            if field in self.fields:
                self.fields[field].disabled = True
