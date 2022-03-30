from django.test import TestCase

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter


class PerimeterModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.perimeter_city = PerimeterFactory(
            name="Grenoble", kind=Perimeter.KIND_CITY, insee_code="38185", department_code="38", region_code="84"
        )
        cls.perimeter_department = PerimeterFactory(
            name="Isère", kind=Perimeter.KIND_DEPARTMENT, insee_code="38", region_code="84"
        )
        cls.perimeter_department_2 = PerimeterFactory(
            name="Guadeloupe", kind=Perimeter.KIND_DEPARTMENT, insee_code="971", region_code="01"
        )
        cls.perimeter_region = PerimeterFactory(
            name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84"
        )
        cls.perimeter_region_2 = PerimeterFactory(name="Guadeloupe", kind=Perimeter.KIND_REGION, insee_code="R01")
        cls.perimeter_country = PerimeterFactory(name="France entière", slug="france", kind=Perimeter.KIND_COUNTRY)

    def test_slug_field(self):
        self.assertEqual(self.perimeter_city.slug, "grenoble-38")
        self.assertEqual(self.perimeter_department.slug, "isere")
        self.assertEqual(self.perimeter_department_2.slug, "guadeloupe")
        self.assertEqual(self.perimeter_region.slug, "auvergne-rhone-alpes-region")
        self.assertEqual(self.perimeter_region_2.slug, "guadeloupe-region")
        self.assertEqual(self.perimeter_country.slug, "france")

    def test_name_display_property(self):
        self.assertEqual(str(self.perimeter_city), "Grenoble (38)")
        self.assertEqual(str(self.perimeter_department), "Isère")
        self.assertEqual(str(self.perimeter_region), "Auvergne-Rhône-Alpes")
        self.assertEqual(str(self.perimeter_region), "France entière")
