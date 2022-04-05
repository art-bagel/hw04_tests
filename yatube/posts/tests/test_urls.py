from http import HTTPStatus

from django.test import TestCase, Client

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
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.author.username}/': HTTPStatus.OK,
            '/unexciting_page/': HTTPStatus.NOT_FOUND
        }
        for address, httpstatus in url_names_httpstatus.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address, follow=True)
                self.assertEqual(response.status_code, httpstatus)

    def test_url_redirect_anonymous_on_login(self):
        """Страницы из url_names_redirect перенаправят
        незарегистрированного пользователя на страницу авторизации.
        """
        self.assertRedirects(
            self.guest_client.get(f'/posts/{self.post.id}/edit/'),
            '/auth/login/' + '?next=' + f'/posts/{self.post.id}/edit/'
        )
        self.assertRedirects(
            self.guest_client.get('/create/'),
            '/auth/login/' + '?next=' + '/create/'
        )

    def test_post_edit_url_available_to_author(self):
        """Страница редактирования поста доступна, только авторизованному
        автору поста.
        """
        response = self.authorized_client_author.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_not_author_on_post(self):
        """Страница редактирования поста, перенаправит всех, кроме автора
         на страницу поста.
        """
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_post_create_url_available_authorized_user(self):
        """Страница создания поста доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/', follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_uses_correct_templates(self):
        """"URL-адрес использует соответствующий шаблон."""
        url_names_templates = {
            '/': 'posts/index.html',
            '/create/': 'posts/create_post.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html'
        }
        for address, template in url_names_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(
                    address, follow=True
                )
                self.assertTemplateUsed(response, template)
