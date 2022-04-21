from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import User, Post


class ViewTestClass(TestCase):

    @classmethod
    def setUpClass(cls):
        """Создаем автора и пользователя."""
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client(enforce_csrf_checks=True)
        self.authorized_client_author.force_login(self.author)
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.author,
        )

    def test_error_page_404(self):
        """Если страница не найдена, должна вернуться кастомная страница."""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_error_page_403(self):
        """Если доступ запрещен, должна вернуться кастомная страница."""
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data={'text': 'Измененный текст'}
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'core/403.html')

    def test_error_csrf_failure(self):
        """Если csrf токен неверный, должна вернуться кастомная
        страница.
        """
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data={'text': 'Измененный текст'}
        )
        self.assertTemplateUsed(response, 'core/403csrf.html')
