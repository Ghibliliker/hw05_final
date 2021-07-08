from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.url_template = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html'
        }

    def test_page_accessible(self):
        for adress in self.url_template.keys():
            with self.subTest(adress=adress):
                response = self.guest_client.get(reverse(adress))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_accessible(self):
        for adress, template in self.url_template.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(reverse(adress))
                self.assertTemplateUsed(response, template)
