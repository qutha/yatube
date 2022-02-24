import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Comment, Group, Post
from django.conf import settings

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormCreateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser',)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание!',
        )
        cls.another_group = Group.objects.create(
            title='Еще одна тестовая группа',
            slug='another_test_slug',
            description='В эту группу добавится пост'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост, который будет изменен',
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост с группой',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        redirect_url = reverse(
            'posts:profile',
            kwargs={'username': self.user.username},
        )
        latest_post = Post.objects.latest('pk')
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(latest_post.text, 'Тестовый пост с группой')
        self.assertEqual(latest_post.group.id, self.group.id)
        self.assertEqual(latest_post.author.username, self.user.username)

    def test_create_post_with_image(self):
        """Валидная форма создает запись с картинкой."""
        posts_count = Post.objects.count()
        gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='image.gif',
            content=gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Пост с картинкой',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        redirect_url = reverse(
            'posts:profile',
            kwargs={'username': self.user.username},
        )
        latest_post = Post.objects.latest('pk')
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(latest_post.text, 'Пост с картинкой')
        self.assertEqual(latest_post.author.username, self.user.username)

    def test_edit_post(self):
        """Редактирование поста работает корректно."""
        form_data = {
            'text': 'Теперь текст поста изменен',
            'group': self.group.id,
        }
        post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk}
        )
        response = self.authorized_client.post(
            post_edit_url,
            data=form_data,
            follow=True,
        )
        redirect_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk},
        )
        latest_post = Post.objects.latest('pk')
        self.assertRedirects(response, redirect_url)
        self.assertEqual(latest_post.text, 'Теперь текст поста изменен')
        self.assertEqual(latest_post.group.id, self.group.id)
        self.assertEqual(latest_post.author.username, self.user.username)

    def test_edit_post_change_group(self):
        """Редактирование группы поста работает корректно."""
        form_data = {
            'text': 'Данный пост поменял свою группу',
            'group': self.another_group.id,
        }
        post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk}
        )
        response = self.authorized_client.post(
            post_edit_url,
            data=form_data,
            follow=True,
        )
        redirect_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk},
        )
        latest_post = Post.objects.latest('pk')
        self.assertRedirects(response, redirect_url)
        self.assertEqual(latest_post.text, 'Данный пост поменял свою группу')
        self.assertEqual(latest_post.group.id, self.another_group.id)
        self.assertEqual(latest_post.author.username, self.user.username)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser', )
        cls.post = Post.objects.create(
            text='Тестовый пост, который будет изменен',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Первый комментарий к посту',
        )
        cls.comment.created -= timedelta(minutes=1)
        cls.comment.save()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_user_can_comment(self):
        """Авторизованный пользователь может оставлять комментарии."""
        comments_amount = Comment.objects.all().count()
        comment_form_data = {
            'text': 'Комментарий к посту',
        }
        add_comment_url = reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.pk},
        )
        redirect_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk},
        )
        response = self.authorized_client.post(
            add_comment_url,
            data=comment_form_data,
            follow=True,
        )
        latest_comment = Comment.objects.latest('created')
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Comment.objects.all().count(), comments_amount + 1)
        self.assertEqual(latest_comment.text, comment_form_data['text'])
        self.assertEqual(latest_comment.author.username, self.user.username)
        self.assertIn(latest_comment, response.context['comments'])
