from django.test import TestCase
from .models import Store

class StoreModelTest(TestCase):
    def test_store_creation(self):
        store = Store.objects.create(
            store_name="Test Store",
            owner_name="John Doe"
        )
        self.assertEqual(str(store), "Test Store - John Doe")
