import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            post=cls.post,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Создание новой записи."""
        posts_count = Post.objects.count()
        form_fields = {
            'text': 'Тестовый пост',
            'group': FormTests.group.id,
            'image': FormTests.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_fields,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': f'{self.user.username}'}
        ))
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                author=FormTests.user,
                group=FormTests.group.id,
                image='posts/small.gif',
            ).exists()
        )

    def test_comment_add(self):
        """Создание нового комментария"""
        comments = Comment.objects.count()
        form_fields = {
            'text': 'Тестовый пост',
            'author': FormTests.user,
            'post': FormTests.post,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{FormTests.post.id}'}
            ),
            data=form_fields,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments + 1)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{FormTests.post.id}'}
        ))

    def test_post_edit(self):
        """Редактирование записи."""
        form_fields = {
            'text': 'Тестовый пост1',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{FormTests.post.id}'}
            ),
            data=form_fields,
            follow=True
        )
        self.assertEqual(Post.objects.get(id=1).text, 'Тестовый пост1')
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{FormTests.post.id}'}
        ))
