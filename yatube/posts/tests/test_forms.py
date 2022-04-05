from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем автора и две группы."""
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group_1 = Group.objects.create(
            title='Первая тестовая группа',
            slug='group_test_1'
        )
        cls.group_2 = Group.objects.create(
            title='Вторая тестовая группа',
            slug='group_test_2'
        )

    def setUp(self):
        """Создаем клиента и пост."""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.author,
            group=self.group_1)

    def test_create_post_form(self):
        """При отправке формы создается новый пост в базе данных.
        После создания происходит редирект на профиль автора.
        """
        post_count = Post.objects.all().count()
        form_data = {
            'text': 'Еще один пост',
            'group': self.group_1.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        self.assertEqual(
            Post.objects.all().count(),
            post_count + 1,
            'Пост не сохранен в базу данных!'
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args=[self.author.username]),
        )

    def test_edit_post_form(self):
        """При отправке формы изменяется пост в базе данных.
        После редактирования происходит редирект на карточку поста.
        """
        form_data = {
            'text': 'Измененный текст поста',
            'group': self.group_2.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_data
        )
        modified_post = Post.objects.get(id=self.post.id)
        self.assertNotEqual(
            modified_post.text,
            self.post.text,
            'Текст поста не изменился!'
        )
        self.assertNotEqual(
            modified_post.group,
            self.post.group,
            'Группа у поста не изменилась!'
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=[self.post.id]),
        )
