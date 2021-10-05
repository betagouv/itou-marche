import factory
from factory.django import DjangoModelFactory

from lemarche.perimeters.models import Perimeter


class PerimeterFactory(DjangoModelFactory):
    class Meta:
        model = Perimeter

    name = factory.Faker("name")
    kind = Perimeter.KIND_CITY
