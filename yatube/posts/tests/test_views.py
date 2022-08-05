from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='group',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': f'{ViewsTests.group.slug}'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': f'{ViewsTests.user.username}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{ViewsTests.post.id}'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{ViewsTests.post.id}'}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                self.authorized_client.force_login(ViewsTests.user)
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, reverse_name)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        for i in range(len(response.context['page_obj'])):
            with self.subTest(i=i):
                self.assertEqual(
                    response.context['page_obj'][i].text, ViewsTests.post.text
                )

    def test_group_list_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': f'{ViewsTests.group.slug}'},
            )
        )
        object_group = response.context['group']
        for i in range(len(response.context['page_obj'])):
            with self.subTest(i=i):
                self.assertEqual(
                    response.context['page_obj'][i].group, object_group
                )

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': f'{ViewsTests.user.username}'}
            )
        )
        profile = response.context['author']
        for i in range(len(response.context['page_obj'])):
            with self.subTest(i=i):
                self.assertEqual(
                    response.context['page_obj'][i].author, profile
                )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{ViewsTests.post.id}'}
            ),
        )
        object_post = response.context['post']
        self.assertEqual(object_post.text, ViewsTests.post.text)

    def test_create_post_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_show_post(self):
        """Созданный пост появляется на страницах index, group_list, profile"""
        response_group_list = (
            self.authorized_client.get(
                reverse(
                    'posts:group_posts',
                    kwargs={'slug': f'{self.group.slug}'})))
        object_post_group_list = response_group_list.context['page_obj'][0]
        self.assertEqual(object_post_group_list, self.post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='group',
            slug='slug',
            description='Тестовое описание',
        )
        objs = [
            Post(
                text=f'Тестовый пост{post}',
                author=cls.user,
                group=cls.group,
            )
            for post in range(13)
        ]
        Post.objects.bulk_create(objs)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_contains_ten_records(self):
        """Первая страница содержит 10 записей"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Вторая страница содержит 3 записи"""
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_cache_home_page(self):
        """Кеш на главной работает правильно"""
        response = self.client.get(reverse('posts:index'))
        object_index1 = response.content
        dpost = Post.objects.filter(id=2)
        dpost.delete()
        response = self.client.get(reverse('posts:index'))
        object_index2 = response.content
        self.assertEqual(object_index1, object_index2)
        cache.clear()
        object_index3 = response.content
        self.assertEqual(object_index3, object_index2)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='follower')
        cls.user_following = User.objects.create_user(username='following')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовый пост',
        )

    def setUp(self):
        self.client_auth_follower = Client()
        self.cliend_auth_following = Client()
        self.client_auth_follower.force_login(self.user_follower)
        self.cliend_auth_following.force_login(self.user_following)

    def test_follow(self):
        """Тест подписки на автора"""
        self.client_auth_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username}
            )
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Тест отписки от автора"""
        self.client_auth_follower.get(
            f'profile/{self.user_following.username}/follow/'
        )
        self.client_auth_follower.get(
            f'profile/{self.user_following.username}/unfollow/'
        )
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_follow_index(self):
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.client_auth_follower.get('/follow/')
        post_text = response.context['page_obj'][0].text
        self.assertEqual(post_text, self.post.text)
