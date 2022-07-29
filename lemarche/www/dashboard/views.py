from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from django.views.generic.edit import CreateView, FormMixin

from lemarche.cms.models import ArticlePage
from lemarche.favorites.models import FavoriteItem, FavoriteList
from lemarche.siaes.models import Siae, SiaeUser, SiaeUserRequest
from lemarche.tenders.models import Tender
from lemarche.users.models import User
from lemarche.utils.s3 import S3Upload
from lemarche.utils.tracker import extract_meta_from_request, track
from lemarche.www.dashboard.forms import (
    ProfileEditForm,
    ProfileFavoriteEditForm,
    SiaeClientReferenceFormSet,
    SiaeEditContactForm,
    SiaeEditInfoForm,
    SiaeEditLinksForm,
    SiaeEditOfferForm,
    SiaeEditSearchForm,
    SiaeImageFormSet,
    SiaeLabelFormSet,
    SiaeOfferFormSet,
    SiaeSearchAdoptConfirmForm,
    SiaeSearchBySiretForm,
    SiaeUserRequestForm,
)
from lemarche.www.dashboard.mixins import (
    FavoriteListOwnerRequiredMixin,
    SiaeMemberRequiredMixin,
    SiaeUserAndNotMemberRequiredMixin,
    SiaeUserRequiredMixin,
)
from lemarche.www.dashboard.tasks import (
    send_siae_user_request_email_to_assignee,
    send_siae_user_request_response_email_to_initiator,
)


class DashboardHomeView(LoginRequiredMixin, DetailView):
    # template_name = "dashboard/home.html"
    context_object_name = "user"

    def get_object(self):
        return self.request.user

    def get_template_names(self):
        if self.request.user.kind == User.KIND_SIAE:
            return ["dashboard/home_siae.html"]
        return ["dashboard/home_buyer.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.kind == User.KIND_SIAE:
            siaes = self.request.user.siaes.all()
            if siaes:
                # context["last_3_tenders"] = Tender.objects.filter_with_siae(siaes).is_live()[:3]
                context["last_3_tenders"] = Tender.objects.filter(tendersiae__siae__in=siaes).distinct()[:3]
            context["last_3_ressources"] = ArticlePage.objects.all()[:3]
        return context


class ProfileEditView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileEditForm
    template_name = "dashboard/profile_edit.html"
    success_message = "Votre profil a été mis à jour."
    success_url = reverse_lazy("dashboard:home")

    def get_object(self):
        return self.request.user


class ProfileFavoriteListView(LoginRequiredMixin, ListView):
    # form_class = ProfileFavoriteEditForm
    template_name = "dashboard/profile_favorite_list.html"
    queryset = FavoriteList.objects.all()
    context_object_name = "favorite_lists"

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.by_user(user=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ProfileFavoriteEditForm()
        return context


class ProfileFavoriteListCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = ProfileFavoriteEditForm
    # success_message = "Votre liste d'achat a été crée avec succès."
    success_url = reverse_lazy("dashboard:profile_favorite_list")

    def form_valid(self, form):
        """Add the User to the FavoriteList."""
        favorite_list = form.save(commit=False)
        favorite_list.user = self.request.user
        favorite_list.save()

        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message(form.cleaned_data),
        )
        # return HttpResponseRedirect(self.get_success_url())  # doesn't work...
        return HttpResponseRedirect(reverse_lazy("dashboard:profile_favorite_list"))

    def get_success_message(self, cleaned_data):
        return mark_safe(f"Votre liste d'achat <strong>{cleaned_data['name']}</strong> a été crée avec succès.")


class ProfileFavoriteListDetailView(FavoriteListOwnerRequiredMixin, DetailView):
    template_name = "dashboard/profile_favorite_list_detail.html"
    context_object_name = "favorite_list"
    queryset = FavoriteList.objects.prefetch_related("siaes").all()


class ProfileFavoriteListEditView(FavoriteListOwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileFavoriteEditForm
    template_name = "siaes/_favorite_list_edit_modal.html"
    success_message = "Votre liste d'achat a été modifiée avec succès."
    # success_url = reverse_lazy("dashboard:profile_favorite_list_detail")

    def get_object(self):
        return get_object_or_404(FavoriteList, slug=self.kwargs.get("slug"))

    def get_success_url(self):
        return reverse_lazy("dashboard:profile_favorite_list_detail", args=[self.kwargs.get("slug")])


class ProfileFavoriteListDeleteView(FavoriteListOwnerRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = "siaes/_favorite_list_delete_modal.html"
    model = FavoriteList
    # success_message = "Votre liste d'achat a été supprimée avec succès."
    success_url = reverse_lazy("dashboard:profile_favorite_list")

    def get_success_message(self, cleaned_data):
        return mark_safe(f"Votre liste d'achat <strong>{self.object.name}</strong> a été supprimée avec succès.")


class ProfileFavoriteItemDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    # FavoriteListOwnerRequiredMixin  # doesn't work because we don't have the FavoriteList slug
    template_name = "siaes/_favorite_item_remove_modal.html"
    model = FavoriteItem
    # success_message = "La structure a été supprimée de votre liste d'achat avec succès."
    success_url = reverse_lazy("dashboard:profile_favorite_list_detail")

    def get_object(self):
        """
        - there should theoretically be only 1 Siae per user's lists (an Siae cannot belong to other list)
        - in the future it could be possible to add an Siae to multiple user lists
        """
        # try:
        #     favorite_list = FavoriteList.objects.get(slug=self.kwargs.get("slug"))
        #     siae = Siae.objects.get(slug=self.kwargs.get("siae_slug"))
        #     return get_object_or_404(FavoriteItem, favorite_list=favorite_list, siae=siae)
        # except:  # noqa
        #     raise Http404
        siae = Siae.objects.get(slug=self.kwargs.get("siae_slug"))
        return get_object_or_404(FavoriteItem, favorite_list__user=self.request.user, siae=siae)

    def get_success_url(self):
        """Redirect to the previous page."""
        request_referer = self.request.META.get("HTTP_REFERER", "")
        if request_referer:
            return request_referer
        return super().get_success_url()

    def get_success_message(self, cleaned_data):
        return mark_safe(
            f"<strong>{self.object.siae.name_display}</strong> a été supprimée de votre liste d'achat avec succès."
        )


class SiaeSearchBySiretView(SiaeUserRequiredMixin, FormMixin, ListView):
    form_class = SiaeSearchBySiretForm
    template_name = "dashboard/siae_search_by_siret.html"
    context_object_name = "siaes"
    # queryset =

    def get_queryset(self):
        """Filter results."""
        filter_form = SiaeSearchBySiretForm(data=self.request.GET)
        results = filter_form.filter_queryset()
        return results

    def get_context_data(self, **kwargs):
        """
        - initialize the form with the query parameters (only if they are present)
        """
        context = super().get_context_data(**kwargs)
        if len(self.request.GET.keys()):
            context["form"] = SiaeSearchBySiretForm(data=self.request.GET)
        return context

    def get(self, request, *args, **kwargs):
        # Track adopt search event
        track(
            "backend",
            "adopt_search",
            meta=extract_meta_from_request(self.request),
        )
        return super().get(request, *args, **kwargs)


class SiaeSearchAdoptConfirmView(SiaeUserAndNotMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeSearchAdoptConfirmForm
    template_name = "dashboard/siae_search_adopt_confirm.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Rattachement confirmé ! Vous pouvez dès à présent mettre à jour sa fiche."

    def get_context_data(self, **kwargs):
        """
        - check if there isn't any pending SiaeUserRequest
        """
        context = super().get_context_data(**kwargs)
        siae_user_pending_request = self.object.siaeuserrequest_set.initiator(self.request.user).pending()
        context["siae_user_pending_request"] = siae_user_pending_request
        return context

    def form_valid(self, form):
        """
        - Siae with user? add the User to the Siae
        - Siae with existing user(s)? go through the invitation workflow
        """
        if not self.object.users.count():
            self.object.users.add(self.request.user)
            return super().form_valid(form)
        else:
            # create SiaeUserRequest + send request email to assignee
            siae_user_request = SiaeUserRequest.objects.create(
                siae=self.object,
                initiator=self.request.user,
                assignee=self.object.users.first(),
                logs=[{"action": "create", "timestamp": timezone.now().isoformat()}],
            )
            send_siae_user_request_email_to_assignee(siae_user_request)
            success_message = (
                f"La demande a été envoyée à {self.object.users.first().full_name}.<br />"
                f"<i>Cet utilisateur ne fait plus partie de la structure ? <a href=\"{reverse_lazy('dashboard:siae_search_by_siret')}?siret={self.object.siret}\">Contactez le support</a></i>"  # noqa
            )
            messages.add_message(self.request, messages.SUCCESS, success_message)
            return HttpResponseRedirect(reverse_lazy("dashboard:home"))

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit", args=[self.kwargs.get("slug")])


class SiaeUsersView(SiaeMemberRequiredMixin, DetailView):
    template_name = "dashboard/siae_users.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()

    def get_context_data(self, **kwargs):
        """
        - check if there isn't any pending SiaeUserRequest
        """
        context = super().get_context_data(**kwargs)
        siae_user_pending_request = self.object.siaeuserrequest_set.assignee(self.request.user).pending()
        context["siae_user_pending_request"] = siae_user_pending_request
        return context


class SiaeEditSearchView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditSearchForm
    template_name = "dashboard/siae_edit_search.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_search", args=[self.kwargs.get("slug")])


class SiaeEditInfoView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditInfoForm
    template_name = "dashboard/siae_edit_info.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_context_data(self, **kwargs):
        """
        - pass s3 image upload config
        - init label form
        """
        context = super().get_context_data(**kwargs)
        s3_upload = S3Upload(kind="siae_logo")
        context["s3_form_values_siae_logo"] = s3_upload.form_values
        context["s3_upload_config_siae_logo"] = s3_upload.config
        if self.request.POST:
            context["label_formset"] = SiaeLabelFormSet(self.request.POST, instance=self.object)
        else:
            context["label_formset"] = SiaeLabelFormSet(instance=self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        label_formset = SiaeLabelFormSet(self.request.POST, instance=self.object)
        if form.is_valid() and label_formset.is_valid():
            return self.form_valid(form, label_formset)
        else:
            return self.form_invalid(form, label_formset)

    def form_valid(self, form, label_formset):
        self.object = form.save()
        label_formset.instance = self.object
        label_formset.save()
        return super().form_valid(form)

    def form_invalid(self, form, label_formset):
        return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_info", args=[self.kwargs.get("slug")])


class SiaeEditOfferView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditOfferForm
    template_name = "dashboard/siae_edit_offer.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_context_data(self, **kwargs):
        """
        - init forms
        - pass s3 image upload config
        """
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["offer_formset"] = SiaeOfferFormSet(self.request.POST, instance=self.object)
            context["client_reference_formset"] = SiaeClientReferenceFormSet(self.request.POST, instance=self.object)
            context["image_formset"] = SiaeImageFormSet(self.request.POST, instance=self.object)
        else:
            context["offer_formset"] = SiaeOfferFormSet(instance=self.object)
            context["client_reference_formset"] = SiaeClientReferenceFormSet(instance=self.object)
            context["image_formset"] = SiaeImageFormSet(instance=self.object)
        s3_upload_client_reference_logo = S3Upload(kind="client_reference_logo")
        context["s3_form_values_client_reference_logo"] = s3_upload_client_reference_logo.form_values
        context["s3_upload_config_client_reference_logo"] = s3_upload_client_reference_logo.config
        s3_upload_siae_image = S3Upload(kind="siae_image")
        context["s3_form_values_siae_image"] = s3_upload_siae_image.form_values
        context["s3_upload_config_siae_image"] = s3_upload_siae_image.config
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        offer_formset = SiaeOfferFormSet(self.request.POST, instance=self.object)
        client_reference_formset = SiaeClientReferenceFormSet(self.request.POST, instance=self.object)
        image_formset = SiaeImageFormSet(self.request.POST, instance=self.object)
        if (
            form.is_valid()
            and offer_formset.is_valid()
            and client_reference_formset.is_valid()
            and image_formset.is_valid()
        ):
            return self.form_valid(form, offer_formset, client_reference_formset, image_formset)
        else:
            return self.form_invalid(form, offer_formset, client_reference_formset, image_formset)

    def form_valid(self, form, offer_formset, client_reference_formset, image_formset):
        self.object = form.save()
        offer_formset.instance = self.object
        offer_formset.save()
        client_reference_formset.instance = self.object
        client_reference_formset.save()
        image_formset.instance = self.object
        image_formset.save()
        return super().form_valid(form)

    def form_invalid(self, form, offer_formset, client_reference_formset, image_formset):
        return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_offer", args=[self.kwargs.get("slug")])


class SiaeEditLinksView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditLinksForm
    template_name = "dashboard/siae_edit_links.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_links", args=[self.kwargs.get("slug")])


class SiaeEditContactView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditContactForm
    template_name = "dashboard/siae_edit_contact.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_contact", args=[self.kwargs.get("slug")])


class SiaeUserRequestConfirm(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeUserRequestForm
    template_name = "siaes/_siae_user_request_confirm_modal.html"
    context_object_name = "siaeuserrequest"
    queryset = SiaeUserRequest.objects.all()
    success_message = "L'utilisateur a été rattaché à votre structure."
    # success_url = reverse_lazy("dashboard:siae_users")

    def get_object(self):
        return get_object_or_404(SiaeUserRequest, id=self.kwargs.get("siaeuserrequest_id"))

    def form_valid(self, form):
        """
        - add user to Siae
        - update SiaeUserRequest
        - notify user
        """
        self.object.siae.users.add(self.object.initiator)
        self.object.response = True
        self.object.response_date = timezone.now()
        self.object.logs.append({"action": "response_true", "timestamp": self.object.response_date.isoformat()})
        self.object.save()
        send_siae_user_request_response_email_to_initiator(self.object, response=True)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_users", args=[self.kwargs.get("slug")])


class SiaeUserRequestCancel(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeUserRequestForm
    template_name = "siaes/_siae_user_request_cancel_modal.html"
    context_object_name = "siaeuserrequest"
    queryset = SiaeUserRequest.objects.all()
    success_message = "L'utilisateur sera informé de votre refus."
    # success_url = reverse_lazy("dashboard:siae_users")

    def get_object(self):
        return get_object_or_404(SiaeUserRequest, id=self.kwargs.get("siaeuserrequest_id"))

    def form_valid(self, form):
        """
        - update SiaeUserRequest
        - notify user
        """
        self.object.response = False
        self.object.response_date = timezone.now()
        self.object.logs.append({"action": "response_false", "timestamp": self.object.response_date.isoformat()})
        self.object.save()
        send_siae_user_request_response_email_to_initiator(self.object, response=False)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_users", args=[self.kwargs.get("slug")])


class SiaeUserDelete(SiaeMemberRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = "siaes/_siae_user_delete_modal.html"
    model = SiaeUser
    # success_message = "L'utilisateur a été supprimé de votre structure."
    # success_url = reverse_lazy("dashboard:siae_users")

    def get_object(self):
        siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        return get_object_or_404(SiaeUser, siae=siae, id=self.kwargs.get("siaeuser_id"))

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_users", args=[self.kwargs.get("slug")])

    def get_success_message(self, cleaned_data):
        return mark_safe(
            f"L'utilisateur <strong>{self.object.user.full_name}</strong> a été supprimé de votre structure avec succès."  # noqa
        )
