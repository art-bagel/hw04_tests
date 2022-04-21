import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User
from yatube import settings

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        """Создаем автора, две группы и загружаемую картику."""
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
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    def setUp(self):
        """Создаем клиента и пост."""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.author,
            group=self.group_1,
            image=None
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

    def test_create_post_form(self):
        """При отправке формы, в базе данных создается новый пост с изображением.
        После создания происходит редирект на профиль автора.
        """
        post_count = Post.objects.all().count()
        form_data = {
            'text': 'Еще один пост',
            'group': self.group_1.id,
            'image': self.uploaded
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
            reverse('posts:profile', args=[self.author.username])
        )
        self.assertTrue(
            Post.objects.filter(
                group_id=form_data['group'],
                text=form_data['text'],
                image='posts/small.gif'
            ).exists(),
            'В созданном посте отсутствует картинка!'
        )

    def test_edit_post_form(self):
        """При отправке формы изменяется пост в базе данных.
        После редактирования происходит редирект на карточку поста.
        """
        form_data = {
            'text': 'Измененный текст поста',
            'group': self.group_2.id,
            'image': self.uploaded
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
        self.assertNotEqual(
            modified_post.image,
            self.post.image,
            'Картинка у поста не изменилась!'
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=[self.post.id]),
        )


class CommentFormTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """Создаем пользователя."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

    def setUp(self):
        """Создаем авторизованного клиента и пост."""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user
        )

    def test_write_comment(self):
        """При отправке формы, в базе данных создается новый комментарий.
        После создания происходит редирект на страницу с постом.
        """
        comments_count = Comment.objects.all().count()
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data={'text': 'Комментарий к посту'}
        )
        self.assertEqual(
            Comment.objects.all().count(),
            comments_count + 1,
            'Комментарий не сохранен в базе данных!'
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=[self.post.id])
        )
