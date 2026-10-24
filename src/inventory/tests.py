"""Tests for the inventory app (Product model and product endpoints).

Known issues documented with ``@expectedFailure`` below:

1. ``ProductAPIView.retrieve`` receives ``request.GET.get("id")`` as a string
   and rejects every id with 400, so a product can never be retrieved by id
   (src/inventory/views.py:16-19, 30-34).
2. ``PATCH`` is not routed with an ``id`` argument, so ``ProductAPIView.patch``
   raises ``TypeError`` (500) when called
   (src/inventory/urls.py:5, src/inventory/views.py:46).
3. There is no ``delete`` handler, so ``DELETE /products`` returns 405 and
   products cannot be soft-deleted through the API
   (src/inventory/views.py).
"""

from decimal import Decimal
from unittest import expectedFailure

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Product

STRONG_PASSWORD = "Str0ngPass!234"

# src/inventory/urls.py uses re_path(r"^(?:|/)$"), which cannot be resolved
# with reverse(): Django's regex_helper.normalize() reduces the route to an
# empty string, so reverse("product-list") raises NoReverseMatch.
PRODUCTS_URL = "/products"


def product_data(**overrides):
    data = {
        "sku_no": "SKU-001",
        "name": "Kopi Susu",
        "description": "Kopi susu gula aren",
        "price": Decimal("15000.00"),
        "quantity": 10,
    }
    data.update(overrides)
    return data


class ProductModelTests(TestCase):
    def test_str_returns_product_name(self):
        product = Product.objects.create(**product_data())

        self.assertEqual(str(product), "Kopi Susu")

    def test_is_deleted_defaults_to_false(self):
        product = Product.objects.create(**product_data())

        self.assertFalse(product.is_deleted)

    def test_sku_no_is_unique(self):
        Product.objects.create(**product_data())

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Product.objects.create(**product_data(name="Kopi Lain"))


class ProductAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="apiuser", password=STRONG_PASSWORD
        )

    def setUp(self):
        self.url = PRODUCTS_URL
        self.client.force_authenticate(user=self.user)

    def create_product(self, **overrides):
        return Product.objects.create(**product_data(**overrides))


class ProductAuthenticationTests(APITestCase):
    def test_list_requires_authentication(self):
        response = self.client.get(PRODUCTS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_requires_authentication(self):
        response = self.client.post(
            PRODUCTS_URL, {"name": "Teh"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProductListTests(ProductAPITestCase):
    def test_list_returns_empty_list_when_no_products(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"], [])
        self.assertEqual(response.data["meta"]["total"], 0)

    def test_list_excludes_soft_deleted_products(self):
        active = self.create_product(sku_no="SKU-ACTIVE")
        self.create_product(
            sku_no="SKU-DELETED", name="Produk Dihapus", is_deleted=True
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["data"]]
        self.assertEqual(ids, [active.id])
        self.assertEqual(response.data["meta"]["total"], 1)

    def test_list_returns_serialized_fields(self):
        product = self.create_product()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data["data"][0]
        self.assertEqual(item["id"], product.id)
        self.assertEqual(item["name"], "Kopi Susu")
        self.assertEqual(item["sku_no"], "SKU-001")
        self.assertEqual(item["price"], "15000.00")
        self.assertEqual(item["quantity"], 10)
        self.assertIn("created_at", item)
        self.assertIn("updated_at", item)


class ProductCreateTests(ProductAPITestCase):
    def test_create_product(self):
        payload = {
            "name": "Teh Melati",
            "sku_no": "SKU-TEH",
            "price": "5000.00",
            "quantity": 4,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertIn("id", response.data["data"])
        self.assertIn("created_at", response.data["data"])

        created = Product.objects.get(sku_no="SKU-TEH")
        self.assertEqual(created.name, "Teh Melati")
        self.assertEqual(created.price, Decimal("5000.00"))
        self.assertEqual(created.quantity, 4)
        self.assertFalse(created.is_deleted)
        # description is not exposed by ProductSerializer.
        self.assertEqual(created.description, "")

    def test_create_missing_required_fields_returns_400(self):
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        for field in ("name", "sku_no", "price", "quantity"):
            self.assertIn(field, response.data["message"])
        self.assertEqual(Product.objects.count(), 0)

    def test_create_duplicate_sku_returns_400(self):
        self.create_product(sku_no="SKU-DUP")

        response = self.client.post(
            self.url,
            {"name": "Duplikat", "sku_no": "SKU-DUP", "price": "1000.00", "quantity": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sku_no", response.data["message"])
        self.assertEqual(Product.objects.count(), 1)


class ProductRetrieveTests(ProductAPITestCase):
    def test_retrieve_with_non_numeric_id_returns_400(self):
        response = self.client.get(self.url, {"id": "abc"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Invalid product ID")

    @expectedFailure
    def test_retrieve_by_id_query_param(self):
        product = self.create_product()

        response = self.client.get(self.url, {"id": product.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], product.id)

        missing = self.client.get(self.url, {"id": product.id + 999})
        self.assertEqual(missing.status_code, status.HTTP_404_NOT_FOUND)


class ProductUpdateTests(ProductAPITestCase):
    @expectedFailure
    def test_patch_product_updates_fields(self):
        product = self.create_product()
        # Return the 500 response instead of raising TypeError.
        self.client.raise_request_exception = False

        response = self.client.patch(self.url, {"name": "Kopi Baru"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.name, "Kopi Baru")


class ProductDeleteTests(ProductAPITestCase):
    @expectedFailure
    def test_delete_product_soft_deletes_it(self):
        product = self.create_product()

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        product.refresh_from_db()
        self.assertTrue(product.is_deleted)
