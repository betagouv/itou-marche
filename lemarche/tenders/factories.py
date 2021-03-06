import datetime
import random

import factory.fuzzy
from django.utils import timezone
from factory.django import DjangoModelFactory

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.sectors.factories import SectorFactory
from lemarche.tenders.models import PartnerShareTender, Tender
from lemarche.users.factories import UserFactory


class TenderFactory(DjangoModelFactory):
    class Meta:
        model = Tender

    title = factory.Faker("name", locale="fr_FR")
    # slug auto-generated
    kind = Tender.TENDER_KIND_QUOTE
    presta_type = []
    response_kind = factory.List(
        [
            factory.fuzzy.FuzzyChoice([key for (key, value) in Tender.RESPONSE_KIND_CHOICES]),
        ]
    )
    description = factory.Faker("paragraph", nb_sentences=5, locale="fr_FR")
    constraints = factory.Faker("paragraph", nb_sentences=5, locale="fr_FR")
    deadline_date = datetime.date.today() + datetime.timedelta(days=10)
    author = factory.SubFactory(UserFactory)
    validated_at = timezone.now()

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

    @factory.post_generation
    def siaes(self, create, extracted, **kwargs):
        if extracted:
            # Add the iterable of groups using bulk addition
            self.siaes.add(*extracted)


class PartnerShareTenderFactory(DjangoModelFactory):
    class Meta:
        model = PartnerShareTender

    name = factory.Faker("name", locale="fr_FR")

    contact_email_list = factory.LazyFunction(
        lambda: [factory.Faker("email", locale="fr_FR") for i in range(random.randint(1, 4))]
    )

    @factory.post_generation
    def perimeters(self, create, extracted, **kwargs):
        if not create:
            self.perimeters.add(*[PerimeterFactory() for i in range(random.randint(1, 9))])
            return

        # Add the iterable of groups using bulk addition
        self.perimeters.add(*extracted)
