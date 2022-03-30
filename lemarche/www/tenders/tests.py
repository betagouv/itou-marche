from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import GEO_RANGE_COUNTRY, GEO_RANGE_CUSTOM, GEO_RANGE_DEPARTMENT, Siae
from lemarche.tenders.factories import TenderFactory
from lemarche.tenders.models import Tender
from lemarche.users.factories import DEFAULT_PASSWORD, UserFactory
from lemarche.users.models import User


class TenderCreateView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER)

    def test_anonymous_user_cannot_create_tender(self):
        url = reverse("tenders:create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_only_non_siae_users_can_create_tender(self):
        # allowed
        self.client.login(email=self.user_buyer.email, password=DEFAULT_PASSWORD)
        url = reverse("tenders:create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # not allowed
        self.client.login(email=self.user_siae.email, password=DEFAULT_PASSWORD)
        url = reverse("tenders:create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/besoins/")


class TenderMatchingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sectors = [SectorFactory() for i in range(10)]
        cls.perimeters = [PerimeterFactory(department_code="75"), PerimeterFactory()]
        # create 2 Siae in Paris
        coords_paris = Point(48.86385199985207, 2.337071483848432)
        siae_one = SiaeFactory(
            is_active=True, geo_range=GEO_RANGE_CUSTOM, coords=coords_paris, geo_range_custom_distance=100
        )
        siae_two = SiaeFactory(
            is_active=True, geo_range=GEO_RANGE_CUSTOM, coords=coords_paris, geo_range_custom_distance=10
        )
        for i in range(5):
            siae_one.sectors.add(cls.sectors[i])
            siae_two.sectors.add(cls.sectors[i + 5])

    def test_matching_tenders_siae(self):
        tender = TenderFactory(sectors=self.sectors)
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 2)

    def test_with_siae_country(self):
        # add Siae with geo_range COUNTRY
        tender = TenderFactory(sectors=self.sectors, perimeters=self.perimeters)
        siae_country = SiaeFactory(is_active=True, geo_range=GEO_RANGE_COUNTRY)
        siae_country.sectors.add(self.sectors[0])
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 3)

    def test_with_siae_department(self):
        # add Siae with geo_range DEPARTMENT
        tender = TenderFactory(sectors=self.sectors, perimeters=self.perimeters)
        siae_department = SiaeFactory(is_active=True, department="75", geo_range=GEO_RANGE_DEPARTMENT)
        siae_department.sectors.add(self.sectors[0])
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 3)

    def test_no_siaes(self):
        tender = TenderFactory(sectors=[SectorFactory()], perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 0)
        tender_marseille = TenderFactory(
            sectors=self.sectors, perimeters=[PerimeterFactory(coords=Point(43.35101634452076, 5.379616625955892))]
        )
        siae_found_list_marseille = Siae.objects.filter_with_tender(tender_marseille)
        self.assertEqual(len(siae_found_list_marseille), 0)
        siae = SiaeFactory(is_active=True, department="75", geo_range=GEO_RANGE_COUNTRY)
        siae_found_list_marseille = Siae.objects.filter_with_tender(tender_marseille)
        self.assertEqual(len(siae_found_list_marseille), 0)
        # add sector
        siae.sectors.add(self.sectors[0])
        siae_found_list_marseille = Siae.objects.filter_with_tender(tender_marseille)
        self.assertEqual(len(siae_found_list_marseille), 1)
        opportunities_for_siae = Tender.objects.filter_with_siae(siae_found_list_marseille[0])
        self.assertEqual(len(opportunities_for_siae), 1)

    def test_with_no_contact_email(self):
        # test when siae doesn't have contact email
        tender = TenderFactory(sectors=self.sectors, perimeters=self.perimeters)
        siae_country = SiaeFactory(is_active=True, geo_range=GEO_RANGE_COUNTRY, contact_email="")
        siae_country.sectors.add(self.sectors[0])
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 2)
        opportunities_for_siae = Tender.objects.filter_with_siae(siae_found_list[0])
        self.assertEqual(len(opportunities_for_siae), 1)

    # def test_number_queries(self):
    #     tender = TenderFactory(sectors=self.sectors)
    #     with self.assertNumQueries(8):
    #         siae_found_list = Siae.objects.filter_with_tender(tender)
    #     self.assertEqual(len(siae_found_list), 2)
