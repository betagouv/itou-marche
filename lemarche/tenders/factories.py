import datetime
import random

import factory.fuzzy
from factory.django import DjangoModelFactory

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.sectors.factories import SectorFactory
from lemarche.tenders.models import Tender


class TenderFactory(DjangoModelFactory):
    class Meta:
        model = Tender

    title = factory.Faker("name", locale="fr_FR")
    # slug auto-generated
    kind = Tender.TENDERS_KIND_QUOTE
    response_kind = factory.fuzzy.FuzzyChoice([key for (key, value) in Tender.RESPONSES_KIND_CHOICES])
    description = factory.Faker("paragraph", nb_sentences=5, locale="fr_FR")
    constraints = factory.Faker("paragraph", nb_sentences=5, locale="fr_FR")
    completion_time = factory.Faker("paragraph", nb_sentences=5, locale="fr_FR")
    deadline_date = datetime.date.today() + datetime.timedelta(days=10)

    @factory.post_generation
    def perimeters(self, create, extracted, **kwargs):
        if not create or not extracted:
            self.perimeters.add(*[PerimeterFactory() for i in range(random.randint(1, 9))])
            return

        # Add the iterable of groups using bulk addition
        self.perimeters.add(*extracted)

    @factory.post_generation
    def sectors(self, create, extracted, **kwargs):
        if not create or not extracted:
            self.sectors.add(*[SectorFactory() for i in range(random.randint(1, 9))])
            return

        # Add the iterable of groups using bulk addition
        self.sectors.add(*extracted)
