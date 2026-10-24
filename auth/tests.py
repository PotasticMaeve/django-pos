"""Tests for the auth app: register, login, token refresh/verify, and logout."""

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

STRONG_PASSWORD = "Str0ngPass!234"


class RegisterViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("register")
        self.payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": STRONG_PASSWORD,
        }

    def test_register_creates_user_with_hashed_password(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"message": "User registered successfully"})

        user = User.objects.get(username=self.payload["username"])
        self.assertEqual(user.email, self.payload["email"])
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertNotEqual(user.password, self.payload["password"])

    def test_register_duplicate_username_returns_400(self):
        User.objects.create_user(username="newuser", password=STRONG_PASSWORD)

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertEqual(User.objects.filter(username="newuser").count(), 1)

    def test_register_weak_password_returns_400(self):
        payload = {**self.payload, "password": "12345678"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_register_missing_required_fields_returns_400(self):
        response = self.client.post(
            self.url, {"email": "only@example.com"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertIn("password", response.data)


class LoginViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password=STRONG_PASSWORD,
        )

    def test_login_returns_access_and_refresh_tokens(self):
        response = self.client.post(
            reverse("token_obtain"),
            {"username": "loginuser", "password": STRONG_PASSWORD},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(response.data["access"])

    def test_login_with_wrong_password_returns_401(self):
        response = self.client.post(
            reverse("token_obtain"),
            {"username": "loginuser", "password": "WrongPassword!234"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)

    def test_login_with_unknown_user_returns_401(self):
        response = self.client.post(
            reverse("token_obtain"),
            {"username": "ghost", "password": STRONG_PASSWORD},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="tokenuser", password=STRONG_PASSWORD
        )

    def _login(self):
        response = self.client.post(
            reverse("token_obtain"),
            {"username": "tokenuser", "password": STRONG_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_refresh_returns_new_tokens(self):
        tokens = self._login()

        response = self.client.post(
            reverse("token_refresh"), {"refresh": tokens["refresh"]}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        # ROTATE_REFRESH_TOKENS is enabled in settings.
        self.assertIn("refresh", response.data)

    def test_verify_valid_access_token(self):
        tokens = self._login()

        response = self.client.post(
            reverse("token_verify"), {"token": tokens["access"]}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_invalid_token_returns_401(self):
        response = self.client.post(
            reverse("token_verify"), {"token": "not-a-token"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="logoutuser", password=STRONG_PASSWORD
        )

    def _login(self):
        response = self.client.post(
            reverse("token_obtain"),
            {"username": "logoutuser", "password": STRONG_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_logout_requires_authentication(self):
        response = self.client.post(
            reverse("logout"), {"refresh": "whatever"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_token_returns_400(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(reverse("logout"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid refresh token")

    def test_logout_with_invalid_refresh_token_returns_400(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("logout"), {"refresh": "not-a-token"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid refresh token")

    def test_logout_blacklists_refresh_token(self):
        tokens = self._login()
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("logout"), {"refresh": tokens["refresh"]}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        self.client.force_authenticate(user=None)
        refresh_response = self.client.post(
            reverse("token_refresh"), {"refresh": tokens["refresh"]}, format="json"
        )

        self.assertEqual(
            refresh_response.status_code, status.HTTP_401_UNAUTHORIZED
        )
        self.assertIn("blacklisted", str(refresh_response.data["detail"]))
