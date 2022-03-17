from django import forms
from django.db.models import Value
from django.db.models.functions import NullIf

from lemarche.sectors.models import Sector
from lemarche.tenders.models import Tender
from lemarche.utils.fields import GroupedModelMultipleChoiceField


EMPTY_CHOICE = (("", ""),)

SECTOR_FORM_QUERYSET = (
    Sector.objects.select_related("group")
    .exclude(group=None)  # sector must have a group !
    .annotate(sector_is_autre=NullIf("name", Value("Autre")))
    .order_by("group__id", "sector_is_autre")
)


class AddTenderForm(forms.ModelForm):

    sectors = GroupedModelMultipleChoiceField(
        label="Secteurs d’activités",
        queryset=SECTOR_FORM_QUERYSET,
        choices_groupby="group",
        to_field_name="slug",
        required=True,
    )

    response_kind = forms.MultipleChoiceField(
        label="Comment répondre",
        choices=Tender.RESPONSES_KIND_CHOICES,
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
            self.errors["perimeters"] = [msg_field_missing.format("Lieux d'exécutions")]
        if "sectors" in self.errors:
            self.errors["sectors"] = [msg_field_missing.format("Secteurs d’activités")]