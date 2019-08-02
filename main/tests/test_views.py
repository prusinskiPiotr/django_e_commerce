from django.test import TestCase
from django.urls import reverse
from main import models
from main import forms
from decimal import Decimal
from unittest.mock import patch
from django.contrib import auth


class TestPage(TestCase):
    def test_homepage_works(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertContains(response, 'BookTime')

    def test_about_us_page_works(self):
        response = self.client.get(reverse("about_us"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about_us.html')
        self.assertContains(response, 'About us')

    def test_contact_us_page_works(self):
        response = self.client.get(reverse("contact_us"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contact_us.html')
        self.assertContains(response, "Contact us")

    def test_products_page_return_active(self):
        models.Product.objects.create(
            name="The cathedral and the bazaar",
            slug="cathedral-bazaar",
            price=Decimal("10.00"),
        )
        models.Product.objects.create(
            name="A Tale of Two cities",
            slug="tale-two-cities",
            price=Decimal("2.00"),
            active=False,
        )
        response = self.client.get(
            reverse("product_list", kwargs={"tag": "all"})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BookTime")

        product_list = models.Product.objects.active().order_by("name")

        self.assertEqual(
            list(response.context["object_list"]),
            list(product_list)
        )

    def test_products_page_filters_by_tags_and_active(self):
        cb = models.Product.objects.create(
            name="The cathedral and the bazaar",
            slug="cathedral-bazaar",
            price=Decimal("10.00"),
        )
        cb.tags.create(name="opensource", slug="opensource")
        
        models.Product.objects.create(
            name="Mictosoft Windows guide",
            slug="microsoft-windows-guide",
            price=Decimal("12.00"),
        )
        response = self.client.get(
            reverse("product_list", kwargs={"tag": "opensource"})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BookTime")

        product_list = (
            models.Product.objects.active().filter(tags__slug="opensource").order_by("name")
        )
        
        self.assertEqual(
            list(response.context["object_list"]),
            list(product_list)
        )

    def test_user_signup_page_loads_correctly(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "signup.html")
        self.assertContains(response, "BookTime")
        self.assertIsInstance(response.context["form"], forms.UserCreationForm)

    def test_user_signup_page_submission_works(self):
        post_data = {
            "email": "user@domain.com",
            "password1": "genericpassword",
            "password2": "genericpassword",
        }
        with patch.object(
            forms.UserCreationForm, "send_mail"
        ) as mock_send:
            response = self.client.post(
                reverse("signup"), post_data
            )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            models.User.objects.filter(email="user@domain.com").exists()
        )
        self.assertTrue(
            auth.get_user(self.client).is_authenticated
        )
        mock_send.assert_called_once()

    def test_address_list_page_returns_only_owned(self):
        user1 = models.User.objects.create_user("user1", "pw432joij")
        user2 = models.User.objects.create_user("user2", "pw432joij")
        models.Address.objects.create(
            user=user1, 
            name="John Doe", 
            address1="flat 2",
            address2="12 Stralz avenue",
            city="London",
            country="uk",
        )
        models.Address.objects.create(
            user=user2,
            name="Janina Doe",
            address1="flat 15",
            address2="Ubahn strasse",
            city="Chicago",
            country="us",
        )
        self.client.force_login(user2)
        response = self.client.get(reverse("address_list"))
        self.assertEqual(response.status_code, 200)
        address_list = models.Address.objects.filter(user=user2)
        self.assertEqual(
            list(response.context["object_list"]),
            list(address_list),
        )

    def test_address_create_stores_user(self):
        user1 = models.User.objects.create_user("user1", "pw432joij")
        post_data = {
            "name": "John Census",
            "address1": "John avenue",
            "address2": "number three",
            "city": "Warsaw",
            "country": "pl",
        }
        self.client.force_login(user1)
        self.client.post(reverse("address_create"), post_data)
        self.assertTrue(models.Address.objects.filter(user=user1).exists())
