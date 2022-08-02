from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create(self):
        """Страница доступна авторизованному пользователю"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail(self):
        """Страница доступна всем"""
        response = self.guest_client.get(f'/posts/{URLTests.post.id}')
        self.assertEqual(
            response.status_code, HTTPStatus.MOVED_PERMANENTLY
        )

    def test_post_edit(self):
        """Страница доступна автору"""
        self.authorized_client.force_login(URLTests.user)
        response = self.authorized_client.get(
            f'/posts/{URLTests.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Несуществующая страница"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_guest_pages(self):
        """Страницы доступны всем"""
        urls = {
            '/',
            f'/group/{URLTests.group.slug}/',
            f'/profile/{URLTests.user.username}/',
        }
        for url in urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{URLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{URLTests.user.username}/': 'posts/profile.html',
            f'/posts/{URLTests.post.id}/': 'posts/post_detail.html',
            f'/posts/{URLTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                self.authorized_client.force_login(URLTests.user)
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_comment_authorized_client(self):
        """Неавторизованные пользователи не могут оставлять комментарии"""
        response = self.guest_client.get(f'/posts/{URLTests.post.id}/comment/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)