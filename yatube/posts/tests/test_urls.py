from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        """Создаем пользователя, группу и пост для тестирования."""
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.not_author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='test_title',
            slug='test_slug'
        )

    def setUp(self):
        """Создаем авторизованного, авторизованного-автора, неавторизованного
        клиента и тестовый пост.
        """
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.not_author)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)
        self.post = Post.objects.create(
            text='test text',
            author=self.author,
            group=self.group,
        )

    def test_url_exists_at_desired_location(self):
        """Страницы из url_names_httpstatus доступны всем пользователям."""
        url_names_httpstatus = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse('posts:group_list',
                    args=[self.group.slug]): HTTPStatus.OK,
            reverse('posts:profile',
                    args=[self.author.username]): HTTPStatus.OK,
            '/unexciting_page/': HTTPStatus.NOT_FOUND
        }
        for address, httpstatus in url_names_httpstatus.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address, follow=True)
                self.assertEqual(response.status_code, httpstatus)

    def test_url_redirect_anonymous_on_login(self):
        """Страница создание и редактирование поста перенаправят
        незарегистрированного пользователя на страницу авторизации.
        """
        self.assertRedirects(
            self.guest_client.get(
                reverse('posts:post_edit', args=[self.post.id])),
            reverse('users:login')
            + '?next=' + reverse('posts:post_edit', args=[self.post.id])
        )
        self.assertRedirects(
            self.guest_client.get(reverse('posts:post_create')),
            reverse('users:login') + '?next=' + reverse('posts:post_create')
        )

    def test_post_edit_url_available_to_author(self):
        """Страница редактирования поста доступна, только авторизованному
        автору поста.
        """
        response = self.authorized_client_author.get(
            reverse('posts:post_edit', args=[self.post.id]), follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_not_author_on_post(self):
        """Страница редактирования поста, перенаправит всех, кроме автора
         на страницу поста.
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[self.post.id]), follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=[self.post.id])
        )

    def test_post_create_url_available_authorized_user(self):
        """Страница создания поста доступна авторизованному пользователю."""
        response = self.authorized_client.get(
            reverse('posts:post_create'), follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_uses_correct_templates(self):
        """"URL-адрес использует соответствующий шаблон."""
        url_names_templates = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:group_list', args=[self.group.slug]):
                'posts/group_list.html',
            reverse('posts:profile', args=[self.author.username]):
                'posts/profile.html',
            reverse('posts:post_detail', args=[self.post.id]):
                'posts/post_detail.html',
            reverse('posts:post_edit', args=[self.post.id]):
                'posts/create_post.html'
        }
        for address, template in url_names_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(
                    address, follow=True
                )
                self.assertTemplateUsed(response, template)
