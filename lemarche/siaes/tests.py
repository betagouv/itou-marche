from bs4 import BeautifulSoup
from django.test import TestCase
from django.urls import reverse

from lemarche.sectors.factories import SectorFactory
from lemarche.siaes.factories import SiaeFactory, SiaeLabelFactory, SiaeOfferFactory
from lemarche.siaes.models import Siae, SiaeUser
from lemarche.users.factories import DEFAULT_PASSWORD, UserFactory
from lemarche.users.models import User


class SiaeModelTest(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        siae = SiaeFactory(name="Ma boite")
        self.assertEqual(str(siae), "Ma boite")

    def test_name_display_property(self):
        siae_without_brand = SiaeFactory(name="Ma raison sociale")
        siae_with_brand = SiaeFactory(name="Ma raison sociale", brand="Mon enseigne")
        self.assertEqual(siae_without_brand.name_display, "Ma raison sociale")
        self.assertEqual(siae_with_brand.name_display, "Mon enseigne")

    def test_siret_display_property(self):
        siae_with_siret = SiaeFactory(siret="12312312312345")
        self.assertEqual(siae_with_siret.siret_display, "123 123 123 12345")
        siae_with_siren = SiaeFactory(siret="123123123")
        self.assertEqual(siae_with_siren.siret_display, "123 123 123")
        siae_with_anormal_siret = SiaeFactory(siret="123123123123")
        self.assertEqual(siae_with_anormal_siret.siret_display, "123123123123")

    def test_geo_range_pretty_display_property(self):
        siae_country = SiaeFactory(geo_range=Siae.GEO_RANGE_COUNTRY)
        self.assertEqual(siae_country.geo_range_pretty_display, "France entière")
        siae_region = SiaeFactory(geo_range=Siae.GEO_RANGE_REGION, region="Guadeloupe")
        self.assertEqual(siae_region.geo_range_pretty_display, "région (Guadeloupe)")
        siae_department = SiaeFactory(geo_range=Siae.GEO_RANGE_DEPARTMENT, region="Bretagne", department="29")
        self.assertEqual(siae_department.geo_range_pretty_display, "département (29)")
        siae_custom = SiaeFactory(
            geo_range=Siae.GEO_RANGE_CUSTOM,
            region="Bretagne",
            department="29",
            city="Quimper",
            geo_range_custom_distance=50,
        )
        self.assertEqual(siae_custom.geo_range_pretty_display, "50 km")
        siae_custom_empty = SiaeFactory(
            geo_range=Siae.GEO_RANGE_CUSTOM, region="Bretagne", department="29", city="Quimper"
        )
        self.assertEqual(siae_custom_empty.geo_range_pretty_display, "non disponible")

    def test_is_missing_content_property(self):
        siae_missing = SiaeFactory(name="Ma boite")
        self.assertTrue(siae_missing.is_missing_content)
        siae_full = SiaeFactory(
            name="Ma boite",
            contact_website="https://example.com",
            contact_email="email@example.com",
            contact_phone="0000000000",
            description="test",
        )
        siae_full_2 = SiaeFactory(
            name="Ma boite",
            contact_website="https://example.com",
            # contact_email="email@example.com",
            # contact_phone="0000000000",
            description="test",
        )
        sector = SectorFactory()
        siae_full.sectors.add(sector)
        SiaeOfferFactory(siae=siae_full)
        SiaeLabelFactory(siae=siae_full)
        siae_full.save()  # to update stats
        self.assertFalse(siae_full.is_missing_content)
        siae_full_2.sectors.add(sector)
        SiaeOfferFactory(siae=siae_full_2)
        SiaeLabelFactory(siae=siae_full_2)
        siae_full_2.save()  # to update stats
        self.assertFalse(siae_full_2.is_missing_content)


class SiaeModelSaveTest(TestCase):
    def setUp(self):
        pass

    def test_slug_field_on_save(self):
        siae = SiaeFactory(name="L'Insertion par le HAUT", department="01")
        self.assertEqual(siae.slug, "linsertion-par-le-haut-01")
        siae = SiaeFactory(name="Structure sans département", department="")
        self.assertEqual(siae.slug, "structure-sans-departement-")
        siae_doublon_1 = SiaeFactory(name="Structure doublon", department="01")
        siae_doublon_2 = SiaeFactory(name="Structure doublon", department="15")
        siae_doublon_3 = SiaeFactory(name="Structure doublon", department="15")
        self.assertEqual(siae_doublon_1.slug, "structure-doublon-01")
        self.assertEqual(siae_doublon_2.slug, "structure-doublon-15")
        self.assertTrue(siae_doublon_3.slug.startswith("structure-doublon-15-"))  # uuid4 at the end
        self.assertTrue(len(siae_doublon_2.slug) < len(siae_doublon_3.slug))
        siae_doublon_10 = SiaeFactory(name="Structure doublon sans departement", department="")
        siae_doublon_11 = SiaeFactory(name="Structure doublon sans departement", department="")
        self.assertEqual(siae_doublon_10.slug, "structure-doublon-sans-departement-")
        self.assertTrue(siae_doublon_11.slug.startswith("structure-doublon-sans-departement--"))  # uuid4 at the end
        self.assertTrue(len(siae_doublon_10.slug) < len(siae_doublon_11.slug))

    def test_update_related_count_on_save(self):
        siae = SiaeFactory()
        SiaeOfferFactory(siae=siae)
        self.assertEqual(siae.offers.count(), 1)
        # self.assertEqual(siae.offer_count, 1)  # won't work, need to call save() method to update stat fields
        siae.save()
        self.assertEqual(siae.offer_count, 1)
        self.assertEqual(siae.user_count, 0)
        self.assertEqual(siae.sector_count, 0)

    def test_update_m2m_count_on_save(self):
        siae = SiaeFactory()
        sector = SectorFactory()
        siae.sectors.add(sector)
        self.assertEqual(siae.sectors.count(), 1)
        # siae.save()  # no need to run save(), m2m_changed signal was triggered above
        self.assertEqual(siae.offer_count, 0)
        self.assertEqual(siae.sector_count, 1)
        self.assertEqual(siae.user_count, 0)

    def test_update_m2m_through_count_on_save(self):
        siae = SiaeFactory()
        user = UserFactory()
        siae.users.add(user)
        self.assertEqual(siae.users.count(), 1)
        # siae.save()  # no need to run save(), m2m_changed signal was triggered above
        self.assertEqual(siae.offer_count, 0)
        self.assertEqual(siae.user_count, 1)
        self.assertEqual(siae.sector_count, 0)
        user_2 = UserFactory()
        siaeuser = SiaeUser(siae=siae, user=user_2)
        siaeuser.save()
        self.assertEqual(siae.users.count(), 1 + 1)
        self.assertEqual(siae.offer_count, 0)
        self.assertEqual(siae.user_count, 1 + 1)
        self.assertEqual(siae.sector_count, 0)

    def test_update_content_fill_date_on_save(self):
        # siae to update
        siae = SiaeFactory(description="")
        user = UserFactory()
        siae.users.add(user)
        sector = SectorFactory()
        siae.sectors.add(sector)
        self.assertEqual(siae.content_filled_basic_date, None)
        siae.description = "test"
        siae.save()
        self.assertNotEqual(siae.content_filled_basic_date, None)
        # siae should be skipped now
        fill_date = siae.content_filled_basic_date
        siae.description = "another test"
        siae.save()
        self.assertEqual(siae.content_filled_basic_date, fill_date)

    def test_update_signup_date_on_save(self):
        siae = SiaeFactory()
        user = UserFactory()
        self.assertEqual(siae.signup_date, None)
        siae.users.add(user)
        self.assertEqual(siae.users.count(), 1)
        # siae.save()  # no need to run save(), m2m_changed signal was triggered above
        self.assertEqual(siae.user_count, 1)
        self.assertNotEqual(siae.signup_date, None)
        # siae should be skipped now
        user_2 = UserFactory()
        signup_date = siae.signup_date
        siae.users.add(user_2)
        # siae.save()  # no need to run save(), m2m_changed signal was triggered above
        self.assertEqual(siae.signup_date, signup_date)

    def test_update_last_updated_fields(self):
        siae = SiaeFactory()
        self.assertEqual(siae.employees_insertion_count, None)
        self.assertEqual(siae.employees_insertion_count_last_updated, None)
        # new value: last_updated field will be set
        siae = Siae.objects.get(id=siae.id)  # we need to fetch it again to pass through the __init__
        siae.employees_insertion_count = 10
        siae.save()
        self.assertEqual(siae.employees_insertion_count, 10)
        self.assertNotEqual(siae.employees_insertion_count_last_updated, None)
        employees_insertion_count_last_updated = siae.employees_insertion_count_last_updated
        # same value: last_updated field will not be updated
        siae = Siae.objects.get(id=siae.id)
        siae.employees_insertion_count = 10
        siae.save()
        self.assertEqual(siae.employees_insertion_count, 10)
        self.assertEqual(siae.employees_insertion_count_last_updated, employees_insertion_count_last_updated)
        # updated value: last_updated field will be updated
        siae = Siae.objects.get(id=siae.id)
        siae.employees_insertion_count = 15
        siae.save()
        self.assertEqual(siae.employees_insertion_count, 15)
        self.assertNotEqual(siae.employees_insertion_count_last_updated, employees_insertion_count_last_updated)


class SiaeModelQuerysetTest(TestCase):
    def setUp(self):
        pass

    def test_is_live_queryset(self):
        SiaeFactory(is_active=True, is_delisted=True)
        SiaeFactory(is_active=False, is_delisted=True)
        SiaeFactory(is_active=True, is_delisted=False)  # live
        SiaeFactory(is_active=False, is_delisted=False)
        self.assertEqual(Siae.objects.count(), 4)
        self.assertEqual(Siae.objects.is_live().count(), 1)
        self.assertEqual(Siae.objects.is_not_live().count(), 3)

    def test_has_user_queryset(self):
        SiaeFactory()
        siae = SiaeFactory()
        user = UserFactory()
        siae.users.add(user)
        self.assertEqual(Siae.objects.count(), 2)
        self.assertEqual(Siae.objects.has_user().count(), 1)

    # def test_annotate_with_user_favorite_list_ids(self):
    # see favorites > tests.py


class SiaeAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.user_staff = UserFactory(kind=User.KIND_ADMIN, is_staff=True, is_superuser=True)
        cls.siae_imported = SiaeFactory(source=Siae.SOURCE_ASP)
        cls.siae_created = SiaeFactory(source=Siae.SOURCE_STAFF_C4_CREATED)

    def test_only_staff_user_can_access_admin(self):
        self.client.login(email=self.user_siae.email, password=DEFAULT_PASSWORD)
        url = reverse("admin:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("/admin/login/" in response.url)

        self.client.login(email=self.user_staff.email, password=DEFAULT_PASSWORD)
        url = reverse("admin:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_staff_user_can_create_siae(self):
        self.client.login(email=self.user_staff.email, password=DEFAULT_PASSWORD)
        url = reverse("admin:siaes_siae_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        name_input = soup.find("input", id="id_name")
        slug_input = soup.find("input", id="id_slug")
        self.assertTrue(name_input.has_attr("required"))  # required
        self.assertEqual(slug_input, None)  # readonly
        form_data = {
            "name": "Created by staff",
            "siret": "12345678910111",
            "kind": "EI",
            "address": "20 Avenue de Ségur",
        }
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, 302)  # 201?
        self.assertEqual(Siae.objects.count(), 2 + 1)
        siae_created_2 = Siae.objects.order_by("id").last()
        self.assertEqual(siae_created_2.source, Siae.SOURCE_STAFF_C4_CREATED)

    def test_staff_user_cannot_update_imported_siae(self):
        self.client.login(email=self.user_staff.email, password=DEFAULT_PASSWORD)
        url = reverse("admin:siaes_siae_change", args=[self.siae_imported.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        name_input = soup.find("input", id="id_name")
        brand_input = soup.find("input", id="id_brand")
        address_input = soup.find("textarea", id="id_address")
        self.assertEqual(name_input, None)  # readonly
        self.assertEqual(brand_input, None)  # readonly
        self.assertEqual(address_input, None)  # readonly

    def test_staff_user_can_update_created_siae(self):
        self.client.login(email=self.user_staff.email, password=DEFAULT_PASSWORD)
        url = reverse("admin:siaes_siae_change", args=[self.siae_created.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        name_input = soup.find("input", id="id_name")
        brand_input = soup.find("input", id="id_brand")
        address_input = soup.find("textarea", id="id_address")
        self.assertEqual(name_input, None)  # readonly
        self.assertTrue(brand_input.has_attr("name"))  # editable
        self.assertTrue(address_input.has_attr("name"))  # editable
