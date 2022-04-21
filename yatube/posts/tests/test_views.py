import shutil
import tempfile
from typing import Any, Dict

from django import forms
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.http.response import HttpResponse
from django.urls import reverse

from posts.models import Comment, Group, Post, User, Follow
from yatube import settings
from yatube.settings import POSTS_PER_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        """Создаем двух авторов, две группы и тестовую картинку."""
        super().setUpClass()
        cls.author_1 = User.objects.create_user(username='author_1')
        cls.author_2 = User.objects.create_user(username='author_2')
        cls.group_1 = Group.objects.create(
            title='Группа_1',
            slug='group_1'
        )
        cls.group_2 = Group.objects.create(
            title='Группа_2',
            slug='group_2'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT)

    def setUp(self):
        """Создаем гостевой и 2 авторизованных клиента.
        Добавляем несколько постов в базу.
        """
        self.guest_client = Client()
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.author_1)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.author_2)
        self.post_1 = Post.objects.create(
            text='test_text_1',
            author=self.author_1,
            group=self.group_1,
            image='tasks/small.gif'
        )
        self.post_2 = Post.objects.create(
            text='test_text_2',
            author=self.author_2,
            group=None,
            image='tasks/small.gif'
        )
        self.post_3 = Post.objects.create(
            text='test_text_3',
            author=self.author_1,
            group=self.group_2,
            image='tasks/small.gif'
        )
        self.comment = Comment.objects.create(
            text='Комментарий к посту 3',
            post=self.post_3,
            author=self.author_2
        )
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list', args=[self.group_1.slug]):
                'posts/group_list.html',
            reverse('posts:profile', args=[self.author_1.username]):
                'posts/profile.html',
            reverse('posts:post_detail', args=[self.post_1.id]):
                'posts/post_detail.html',
            reverse('posts:post_edit', args=[self.post_1.id]):
                'posts/create_post.html',
            reverse('posts:post_create'):
                'posts/create_post.html'

        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_1.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client_1.get(reverse('posts:index'))
        posts_from_context = response.context.get('page_obj').object_list
        expected_posts = list(Post.objects.all())
        self.assertEqual(posts_from_context, expected_posts,
                         'Главная страница выводит не все посты!'
                         )
        self.assertTrue(posts_from_context[0].image)

    def test_home_page_is_cached(self):
        """Домашняя страница закеширована."""
        response_one = self.authorized_client_2.get(reverse('posts:index'))
        self.post_3.delete()
        response_two = self.authorized_client_1.get(reverse('posts:index'))
        self.assertEqual(response_one.content, response_two.content,
                         'Главная страница не закеширована.'
                         )
        cache.clear()
        response_tree = self.authorized_client_1.get(reverse('posts:index'))
        self.assertNotEqual(response_tree.content, response_one.content)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client_1.get(
            reverse('posts:group_list', args=[self.group_2.slug])
        )
        posts_from_context = response.context.get('page_obj').object_list
        group_from_context = response.context.get('group')
        expected_posts = list(Post.objects.filter(group_id=self.group_2.id))
        self.assertEqual(posts_from_context, expected_posts,
                         'Посты в контексте имеют разное значение поле групп!'
                         )
        self.assertEqual(group_from_context, self.group_2,
                         'Страница группы отличается от группы из контекста!'
                         )
        self.assertTrue(posts_from_context[0].image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client_1.get(
            reverse('posts:profile', args=[self.author_1.username])
        )
        posts_from_context = response.context.get('page_obj').object_list
        author_from_context = response.context.get('author')
        expected_posts = list(Post.objects.filter(author_id=self.author_1.id))
        self.assertEqual(posts_from_context, expected_posts,
                         'Посты из контекста пренадлежать другому автору!'
                         )
        self.assertEqual(author_from_context, self.author_1,
                         'Автор из контекста не совпадает с профилем!'
                         )
        self.assertTrue(posts_from_context[0].image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField
        }
        response = self.authorized_client_1.get(
            reverse('posts:post_detail', args=[self.post_3.id])
        )
        post_from_context = response.context.get('post')
        number_posts_author = response.context.get('number_posts_author')
        number_comments = len(response.context.get('comments'))
        expected_number_post = Post.objects.filter(
            author=self.author_1).count()
        expected_number_comments = Comment.objects.filter(
            post_id=self.post_3.id).count()
        self.assertEqual(post_from_context, self.post_3,
                         'Пост из контекста не совпадает с ожидаемым!'
                         )
        self.assertEqual(number_posts_author, expected_number_post,
                         'Количество постов автора из контекста неверно!'
                         )
        self.assertEqual(number_comments, expected_number_comments,
                         'Количество комментариев к посту не совпадает!'
                         )
        self.assertTrue(post_from_context.image,
                        'Картинка поста не передается в контексте!'
                        )
        self._check_correct_form_from_context(response, form_fields)

    def test_create_comment_show_on_post_page(self):
        """Созданный комментарий выводится на странице поста."""
        self.authorized_client_1.post(
            reverse('posts:add_comment', args=[self.post_2.id]),
            data={'text': 'Новый комментарий'}
        )
        response = self.authorized_client_1.get(
            reverse('posts:post_detail', args=[self.post_2.id])
        )
        self.assertEqual(response.context.get('comments')[0].text,
                         'Новый комментарий',
                         'Комментарий не выводится на странице поста!'
                         )

    def test_anonymous_can_not_comment(self):
        """Анонимный пользователь не может комментировать посты."""
        comments_count = Comment.objects.filter(post_id=self.post_1.id).count()
        self.guest_client.post(
            reverse('posts:add_comment', args=[self.post_1.id]),
            data={'text': 'Новый комментарий к посту'}
        )
        self.assertNotEqual(
            Comment.objects.filter(post_id=self.post_1.id).count(),
            comments_count + 1,
            'Неавторизованный клиент не может оставлять комментарии!'
        )

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        response = self.authorized_client_1.get(reverse('posts:post_create'))
        self._check_correct_form_from_context(response, form_fields)

    def test_new_post_show_on_different_page(self):
        """Новый пост выводится на главной, в выбранной группе,
        и в профайле автора. Не выводится в других группах.
        """
        form_data = {
            'text': 'new_post',
            'group': self.group_1.id
        }
        url_names_assert_method = {
            reverse('posts:index'): self.assertEqual,
            reverse('posts:group_list',
                    args=[self.group_1.slug]): self.assertEqual,
            reverse('posts:profile',
                    args=[self.author_1.username]): self.assertEqual,
            reverse('posts:group_list',
                    args=[self.group_2.slug]): self.assertNotEqual
        }
        self.authorized_client_1.post(
            reverse('posts:post_create'),
            data=form_data
        )
        new_post = Post.objects.latest('id')
        for address, assert_method in url_names_assert_method.items():
            with self.subTest(address=address):
                cache.clear()
                response = self.authorized_client_1.get(address, follow=True)
                last_post_on_page = response.context.get('page_obj')[0]
                assert_method(last_post_on_page, new_post)

    def test_post_edit_show_correct_context(self):
        """Шаблон страницы post_edit сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        response = self.authorized_client_1.get(
            reverse('posts:post_edit', args=[self.post_1.id])
        )
        self._check_correct_form_from_context(response, form_fields)

    def _check_correct_form_from_context(self, response: HttpResponse,
                                         form_fields: Dict[str, Any]
                                         ) -> None:
        """Проверяем корректность формы передаваемой в контексте."""
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """Создаем автора и группу."""
        super().setUpClass()
        cls.author = User.objects.create_user(username='author_1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='group_test'
        )

    def setUp(self):
        """Создаем клиента и 15 постов."""
        self.client = Client()
        self.number_create_posts = 15
        posts = []
        for i in range(self.number_create_posts):
            posts.append(Post.objects.create(
                text=f'test_text_{i}',
                author=self.author,
                group=self.group))

    def test_index_page(self):
        """Проверяет пагинацию главной страницы."""
        self._check_correct_pagination(reverse('posts:index'), POSTS_PER_PAGE)
        self._check_correct_pagination(
            reverse('posts:index') + '?page=2',
            self.number_create_posts % POSTS_PER_PAGE
        )

    def test_group_list_page(self):
        """Проверяет пагинацию страницы списка групп."""
        self._check_correct_pagination(
            reverse('posts:group_list', args=[self.group.slug]),
            POSTS_PER_PAGE
        )
        self._check_correct_pagination(
            reverse('posts:group_list', args=[self.group.slug]) + '?page=2',
            self.number_create_posts % POSTS_PER_PAGE
        )

    def test_profile_page(self):
        """Проверяет пагинацию страницы профиля автора."""
        self._check_correct_pagination(
            reverse('posts:profile', args=[self.author.username]),
            POSTS_PER_PAGE
        )
        self._check_correct_pagination(
            reverse('posts:profile', args=[self.author.username]) + '?page=2',
            self.number_create_posts % POSTS_PER_PAGE
        )

    def _check_correct_pagination(self, url_page: str, expected: int) -> None:
        """Сравнивает количество постов на запрошенной странице с ожидаемым
        результатом.
        """
        cache.clear()
        response = self.client.get(url_page)
        number_posts_on_page = len(response.context['page_obj'])
        self.assertEqual(number_posts_on_page, expected)


class FollowViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        """Создаем двух авторов, две группы и тестовую картинку."""
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='user_1')
        cls.user_2 = User.objects.create_user(username='user_2')
        cls.author_1 = User.objects.create_user(username='author_1')
        cls.author_2 = User.objects.create_user(username='author_2')
        cls.group_1 = Group.objects.create(
            title='Группа_1',
            slug='group_1'
        )
        cls.group_2 = Group.objects.create(
            title='Группа_2',
            slug='group_2'
        )

    def setUp(self):
        """Создаем гостевой и авторизованный клиент.
        Добавляем несколько постов в базу.
        """
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.user_1)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        self.authorized_client_author_1 = Client()
        self.authorized_client_author_1.force_login(self.author_1)
        self.authorized_client_author_2 = Client()
        self.authorized_client_author_2.force_login(self.author_2)
        self.post_1 = Post.objects.create(
            text='test_text_1',
            author=self.author_1,
            group=self.group_1,
        )
        self.post_2 = Post.objects.create(
            text='test_text_2',
            author=self.author_2,
            group=self.group_2,
        )
        self.authorized_client_1.get(
            reverse('posts:profile_follow', args=[self.author_1.username])
        )
        self.authorized_client_2.get(
            reverse('posts:profile_follow', args=[self.author_2.username])
        )

    def test_authorized_user_can_subscribe(self):
        """Авторизованный пользователь может подписаться на автора."""
        is_subscribe = Follow.objects.filter(author_id=self.author_1.id,
                                             user_id=self.user_1.id
                                             ).exists()
        self.assertTrue(is_subscribe, 'Пользователь не смог подписаться!')

    def test_authorized_user_can_unsubscribe(self):
        """Авторизованный пользователь может отписаться от автора."""
        self.authorized_client_1.get(
            reverse('posts:profile_unfollow', args=[self.author_1.username])
        )
        is_subscribe = Follow.objects.filter(author_id=self.author_1.id,
                                             user_id=self.user_1.id
                                             ).exists()
        self.assertFalse(is_subscribe, 'Пользователь не смог отписаться!')

    def test_appears_on_subscribers(self):
        """Новый пост автора появляется в ленте у подписчиков."""
        new_post = Post.objects.create(
            text='new_post',
            author=self.author_1,
        )
        response = self.authorized_client_1.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(response.context.get('page_obj')[0], new_post,
                         'Пост не отображается в ленте у подписчика!'
                         )

    def test_does_not_appear_on_non_subscriber(self):
        """Новый пост не появляется у тех, кто не подписался."""
        new_post = Post.objects.create(
            text='new_post_2',
            author=self.author_1,
        )
        response = self.authorized_client_2.get(
            reverse('posts:follow_index')
        )
        self.assertNotEqual(response.context.get('page_obj')[0], new_post,
                            'Новый пост отображается у тех, кто не подписался!'
                            )
