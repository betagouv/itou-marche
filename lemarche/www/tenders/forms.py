from datetime import date

from django import forms

from lemarche.sectors.models import Sector
from lemarche.tenders.models import Tender
from lemarche.utils.fields import GroupedModelMultipleChoiceField


class AddTenderForm(forms.ModelForm):
    sectors = GroupedModelMultipleChoiceField(
        label=Sector._meta.verbose_name_plural,
        queryset=Sector.objects.form_filter_queryset(),
        choices_groupby="group",
        to_field_name="slug",
        required=True,
    )

    response_kind = forms.MultipleChoiceField(
        label="Comment répondre",
        choices=Tender.RESPONSE_KIND_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Tender
        fields = [
            "kind",
            "title",
            "description",
            "sectors",
            "constraints",
            "amount",
            # perimeters are generated by js
            "perimeters",
            "external_link",
            "response_kind",
            "deadline_date",
            "start_working_date",
            "contact_first_name",
            "contact_last_name",
            "contact_email",
            "contact_phone",
            "is_country_area",
        ]

        widgets = {
            # "perimeters": forms.HiddenInput(),
            "deadline_date": forms.widgets.DateInput(attrs={"class": "form-control", "type": "date"}),
            "start_working_date": forms.widgets.DateInput(attrs={"class": "form-control", "type": "date"}),
            "kind": forms.RadioSelect(),
        }

    def clean(self):
        super().clean()
        msg_field_missing = "{} est un champ obligatoire"
        if "perimeters" in self.errors:
            self.add_error("perimeters", msg_field_missing.format("Lieux d'exécution"))
        if "sectors" in self.errors:
            self.add_error("sectors", msg_field_missing.format(Sector._meta.verbose_name_plural))
        today = date.today()
        if self.cleaned_data.get("deadline_date") and (self.cleaned_data.get("deadline_date") < today):
            self.add_error(
                "deadline_date", "La date de clôture des réponses ne doit pas être antérieure à aujourd'hui."
            )

        if (
            self.cleaned_data.get("deadline_date")
            and self.cleaned_data.get("start_working_date")
            and (self.cleaned_data.get("start_working_date") < self.cleaned_data.get("deadline_date"))
        ):
            self.add_error(
                "start_working_date",
                "La date idéale de début des prestations ne doit pas être antérieure de clôture des réponses.",
            )
