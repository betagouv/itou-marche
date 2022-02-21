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
        label="Secteur d’activité2",
        queryset=SECTOR_FORM_QUERYSET,
        choices_groupby="group",
        to_field_name="slug",
        required=False,
    )

    class Meta:
        model = Tender
        fields = [
            "kind",
            "title",
            "description",
            "sectors",
            "constraints",
            "completion_time",
            "perimeters",
            "external_link",
            "kind_response",
            "deadline_date",
            "start_working_date",
        ]

        widgets = {
            "perimeter": forms.HiddenInput(),
            "deadline_date": forms.widgets.DateInput(attrs={"class": "form-control", "type": "date"}),
            "start_working_date": forms.widgets.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # perimeter = self.data.get("perimeter", "")
        # if not perimeter:
        #     raise forms.ValidationError(
        #         {"perimeter": "Périmètre inconnu. Veuillez en choisir un dans la liste, ou effacer le texte."}
        #     )
        # if perimeter:
        #     self.cleaned_data["perimeter"] = self.get_perimeter()
        print(cleaned_data)
        import ipdb

        ipdb.set_trace()
        return self.cleaned_data

    # def get_perimeter(self):
    #     """
    #     Method to extract the perimeter searched by the user.
    #     Useful to avoid duplicate DB queries on the Perimeter model.
    #     """
    #     perimeter = None
    #     search_perimeter = self.data.get("perimeter", None)
    #     search_perimeter_name = self.data.get("perimeter_name", None)
    #     # A valid perimeter search must have both the `perimeter` & `perimeter_name` fields in the querystring
    #     if search_perimeter and search_perimeter_name:
    #         try:
    #             perimeter = Perimeter.objects.get(slug=search_perimeter)
    #         except Perimeter.DoesNotExist:
    #             pass
    #     return perimeter
