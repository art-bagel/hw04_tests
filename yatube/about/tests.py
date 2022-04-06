from http import HTTPStatus

from django.test import TestCase, Client


class StaticURLTests(TestCase):

    def setUp(self):
        """Устанавливаем данные для тестирования."""
        self.guest_client = Client()

    def test_author_url_exists_at_desired_location(self):
        """Страница /author/ доступна всем пользователям."""
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech_url_exists_at_desired_location(self):
        """Страница /tech/ доступна всем пользователям."""
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_uses_correct_templates(self):
        """URL-адрес /author/ использует соответствующий шаблон."""
        response = self.guest_client.get('/about/author/')
        self.assertTemplateUsed(response, 'about/author.html')

    def test_tech_uses_correct_templates(self):
        """URL-адрес /tech/ использует соответствующий шаблон."""
        response = self.guest_client.get('/about/tech/')
        self.assertTemplateUsed(response, 'about/tech.html')
