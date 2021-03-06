from datetime import datetime

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from lemarche.common.admin import admin_site
from lemarche.perimeters.admin import PerimeterRegionFilter
from lemarche.tenders.forms import TenderAdminForm
from lemarche.tenders.models import PartnerShareTender, Tender
from lemarche.utils.fields import pretty_print_readonly_jsonfield
from lemarche.www.tenders.tasks import send_confirmation_published_email_to_author, send_tender_emails_to_siaes


class ResponseKindFilter(admin.SimpleListFilter):
    title = Tender._meta.get_field("response_kind").verbose_name
    parameter_name = "response_kind"

    def lookups(self, request, model_admin):
        return Tender.RESPONSE_KIND_CHOICES

    def queryset(self, request, queryset):
        lookup_value = self.value()
        if lookup_value:
            queryset = queryset.filter(response_kind__contains=[lookup_value])
        return queryset


def update_and_send_tender_task(tender: Tender):
    # 1) validate the tender
    tender.validated_at = datetime.now()
    tender.save()
    # 2) find the matching Siaes? done in Tender post_save signal
    # 3) send the tender to all matching Siaes
    send_tender_emails_to_siaes(tender)
    send_confirmation_published_email_to_author(tender, nb_matched_siaes=tender.siaes.count())


@admin.register(Tender, site=admin_site)
class TenderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "is_validate",
        "title",
        "user_with_link",
        "kind",
        "deadline_date",
        "start_working_date",
        "nb_siae",
        "nb_siae_email_send",
        "nb_siae_detail_display",
        "nb_siae_contact_click",
        "created_at",
    ]
    list_filter = ["kind", "deadline_date", "start_working_date", ResponseKindFilter]
    # filter on "perimeters"? (loads ALL the perimeters... Use django-admin-autocomplete-filter instead?)
    search_fields = ["id", "title", "author__id", "author__email"]
    search_help_text = "Cherche sur les champs : ID, Titre, Auteur (ID, E-mail)"
    ordering = ["-created_at"]

    autocomplete_fields = ["perimeters", "sectors", "author"]
    readonly_fields = [
        "nb_siae",
        "nb_siae_email_send",
        "nb_siae_detail_display",
        "nb_siae_contact_click",
        "siae_interested_list_last_seen_date",
        "logs_display",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": ("title", "slug", "kind"),
            },
        ),
        (
            "D??tails",
            {
                "fields": (
                    "description",
                    "constraints",
                    "sectors",
                    "presta_type",
                    "is_country_area",
                    "perimeters",
                    "external_link",
                    "amount",
                    "response_kind",
                    "deadline_date",
                    "start_working_date",
                ),
            },
        ),
        (
            "Contact",
            {
                "fields": ("author", "contact_first_name", "contact_last_name", "contact_email", "contact_phone"),
            },
        ),
        (
            "Stats",
            {
                "fields": (
                    "nb_siae",
                    "nb_siae_email_send",
                    "nb_siae_detail_display",
                    "nb_siae_contact_click",
                    "logs_display",
                ),
            },
        ),
        ("Info", {"fields": ("created_at", "updated_at")}),
    )

    change_form_template = "tenders/admin_change_form.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.with_siae_stats()
        return qs

    def get_changeform_initial_data(self, request):
        """
        Default values in add form.
        """
        return {"source": Tender.SOURCE_STAFF_C4_CREATED}

    def is_validate(self, tender: Tender):
        return tender.validated_at is not None

    is_validate.boolean = True
    is_validate.short_description = "Valid??"

    def user_with_link(self, tender):
        url = reverse("admin:users_user_change", args=[tender.author_id])
        return format_html(f'<a href="{url}">{tender.author}</a>')

    user_with_link.short_description = "Auteur"
    user_with_link.admin_order_field = "author"

    def nb_siae(self, tender):
        url = reverse("admin:siaes_siae_changelist") + f"?tenders__in={tender.id}"
        return format_html(f'<a href="{url}">{getattr(tender, "siae_count", 0)}</a>')

    nb_siae.short_description = "Structures concern??es"
    nb_siae.admin_order_field = "siae_count"

    def nb_siae_email_send(self, tender):
        url = (
            reverse("admin:siaes_siae_changelist")
            + f"?tenders__in={tender.id}&tendersiae__email_send_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(tender, "siae_email_send_count", 0)}</a>')

    nb_siae_email_send.short_description = "S. contact??es"
    nb_siae_email_send.admin_order_field = "siae_email_send_count"

    def nb_siae_detail_display(self, tender):
        url = (
            reverse("admin:siaes_siae_changelist")
            + f"?tenders__in={tender.id}&tendersiae__detail_display_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(tender, "siae_detail_display_count", 0)}</a>')

    nb_siae_detail_display.short_description = "S. vues"
    nb_siae_detail_display.admin_order_field = "siae_detail_display_count"

    def nb_siae_contact_click(self, tender):
        url = (
            reverse("admin:siaes_siae_changelist")
            + f"?tenders__in={tender.id}&tendersiae__contact_click_date__isnull=False"
        )
        return format_html(f'<a href="{url}">{getattr(tender, "siae_contact_click_count", 0)}</a>')

    nb_siae_contact_click.short_description = "S. int??ress??es"
    nb_siae_contact_click.admin_order_field = "siae_contact_click_count"

    def logs_display(self, tender=None):
        if tender:
            return pretty_print_readonly_jsonfield(tender.logs)
        return "-"

    logs_display.short_description = Tender._meta.get_field("logs").verbose_name

    def response_change(self, request, obj: Tender):
        if "_validate_tender" in request.POST:
            update_and_send_tender_task(tender=obj)
            self.message_user(request, "Ce d??p??t de besoin a ??t?? valid?? et envoy?? aux structures")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)


@admin.register(PartnerShareTender, site=admin_site)
class PartnerShareTenderAdmin(admin.ModelAdmin, DynamicArrayMixin):
    form = TenderAdminForm
    list_display = ["id", "name", "perimeters_string", "amount_in", "created_at"]
    list_filter = [PerimeterRegionFilter, "amount_in"]
    search_fields = ["id", "name"]
    search_help_text = "Cherche sur les champs : ID, Nom"

    readonly_fields = ["perimeters_string", "logs_display", "created_at", "updated_at"]
    autocomplete_fields = ["perimeters"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related("perimeters")
        return qs

    def perimeters_string(self, partnersharetender):
        return partnersharetender.perimeters_list_string

    perimeters_string.short_description = "P??rim??tres"

    def logs_display(self, partnersharetender=None):
        if partnersharetender:
            return pretty_print_readonly_jsonfield(partnersharetender.logs)
        return "-"

    logs_display.short_description = PartnerShareTender._meta.get_field("logs").verbose_name
