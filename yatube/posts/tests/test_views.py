import shutil
import tempfile
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import ImageFieldFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache.utils import make_template_fragment_key

from ..forms import PostForm
from ..models import Group, Post, Follow
from ..views import POSTS_AMOUNT

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mktemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.empty_group = Group.objects.create(
            title='Пустая тестовая группа',
            slug='empty_group',
            description='Описание пустой группы',
        )
        cls.post_with_group = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для поста с группой',
            group=cls.group,
        )
        cls.post_without_group = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для поста без группы',
        )
        cls.image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='image.gif',
            content=cls.image,
            content_type='image/gif',
        )
        cls.post_with_image = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для поста с картинкой',
            group=cls.group,
        )
        cls.user_to_follow = User.objects.create_user(
            username='user-to-follow',
        )
        cls.post_follow = Post.objects.create(
            author=cls.user_to_follow,
            text=(
                'Пост пользователя, на которого подпишутся, а потом отпишутся'
            ),
        )
        cls.user_without_followers = User.objects.create_user(
            username='user-without-followers',
        )
        cls.post_without_follow = Post.objects.create(
            author=cls.user_without_followers,
            text=(
                'По всей видимости ужасный пост'
            ),
        )
        cls.post_with_group.created += timedelta(minutes=1)
        cls.post_without_group.created += timedelta(minutes=2)
        cls.post_with_image.created += timedelta(minutes=3)
        cls.post_follow.created += timedelta(minutes=4)
        cls.post_without_follow.created += timedelta(minutes=5)
        cls.post_with_group.save()
        cls.post_without_group.save()
        cls.post_with_image.save()
        cls.post_follow.save()
        cls.post_without_follow.save()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        template_pages_names = {
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post_with_group.pk}
            ): 'posts/create_post.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post_with_group.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): 'posts/profile.html',
        }
        for reverse_name, template in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_follow = response.context['page_obj'][-4]
        post_without_follow = response.context['page_obj'][-5]
        self.are_posts_correct(response)
        self.assertEqual(post_follow, self.post_follow)
        self.assertEqual(post_without_follow, self.post_without_follow)

    def test_group_posts_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug},
            )
        )
        self.are_group_posts_fields_correct(response)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post_with_group.pk},
            )
        )
        self.assertEqual(response.context['author'].username, 'TestUser')
        self.assertEqual(
            response.context['post'], self.post_with_group
        )
        self.assertEqual(response.context['posts_amount'], 3)
        self.assertEqual(response.context['group'], self.group)
        self.assertIsNone(response.context.get('is_edit'), None)

    def test_post_with_image_detail_correct_context(self):
        """Страница с постом с картинкой сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post_with_image.pk},
            )
        )
        post = response.context['post']
        self.assertEqual(response.context['author'].username, 'TestUser')
        self.assertEqual(
            post, self.post_with_image
        )
        self.assertEqual(response.context['posts_amount'], 3)
        self.assertEqual(response.context['group'], self.group)
        self.assertIsInstance(post.image, ImageFieldFile)
        self.assertIsNone(response.context.get('is_edit'), None)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        author_posts_amount = self.user.posts.all().count()
        self.assertEqual(response.context['author'].username, 'TestUser')
        self.assertEqual(response.context['posts_amount'], author_posts_amount)
        self.are_posts_correct(response)

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIsNone(response.context.get('is_edit', None))

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post_without_group.pk},
            )
        )
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertTrue(response.context['is_edit'])
        self.assertIsInstance(response.context['is_edit'], bool)

    def test_empty_group_is_empty(self):
        """Группа empty_group не имеет постов"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': 'empty_group'}
            )
        )
        posts = response.context.get('page_obj').object_list
        self.assertEqual(len(posts), 0)

    def test_cache_on_index_page(self):
        """Кэширование работает на главной странице"""
        post = Post.objects.create(
            text='Самый уникальный текст, который есть только в этом посте',
            author=self.user,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        page_obj = response.context['page_obj']
        first_cache_index = cache.get(
            make_template_fragment_key('index_page', [page_obj.number])
        )
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        page_obj = response.context['page_obj']
        second_cache_index = cache.get(
            make_template_fragment_key('index_page', [page_obj.number])
        )
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        page_obj = response.context['page_obj']
        third_cache_index = cache.get(
            make_template_fragment_key('index_page', [page_obj.number])
        )
        self.assertIn(post.text, first_cache_index)
        self.assertIn(post.text, second_cache_index)
        self.assertNotIn(post.text, third_cache_index)

    def test_authorized_client_can_follow(self):
        """Авторизованный клиент может подписываться."""
        posts_amount = Post.objects.filter(
            author__following__user=self.user
        ).count()
        Follow.objects.create(user=self.user, author=self.user_to_follow)
        self.assertEqual(
            Post.objects.filter(author__following__user=self.user).count(),
            posts_amount + 1
        )

    def test_authorized_client_can_unfollow(self):
        """Авторизованный клиент может отписываться."""
        Follow.objects.create(user=self.user, author=self.user_to_follow)
        posts_amount = Post.objects.filter(
            author__following__user=self.user
        ).count()
        Follow.objects.filter(
            user=self.user, author=self.user_to_follow
        ).delete()
        self.assertEqual(
            Post.objects.filter(author__following__user=self.user).count(),
            posts_amount - 1
        )

    def test_followed_post_appears_in_feed(self):
        """Новая запись появляется в ленте, на кого подписан клиент."""
        Follow.objects.create(user=self.user, author=self.user_to_follow)
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        new_followed_post = Post.objects.create(
            author=self.user_to_follow,
            text=(
                'Ужасный код, с этим надо что-то делать'
            ),
        )
        new_unfollowed_post = Post.objects.create(
            author=self.user_without_followers,
            text=(
                'Этот пост противоречит взглядам автора сайта'
            ),
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(new_followed_post, response.context['page_obj'])
        self.assertNotIn(new_unfollowed_post, response.context['page_obj'])

    def are_group_posts_fields_correct(self, response):
        """Проверка полей у поста"""
        group = response.context['group']
        posts = response.context['page_obj']
        post_with_image = posts[0]
        self.assertIsInstance(post_with_image.image, ImageFieldFile)
        self.assertEqual(group.slug, 'test_slug')
        self.assertEqual(group.title, 'Тестовая группа')
        self.assertEqual(group.description, 'Тестовое описание')
        for post in posts:
            with self.subTest(post=post):
                self.assertEqual(post.group.slug, 'test_slug')

    def are_posts_correct(self, response):
        """Проверка всех постов"""
        post_with_group = response.context['page_obj'][-1]
        post_without_group = response.context['page_obj'][-2]
        post_with_image = response.context['page_obj'][-3]
        self.assertEqual(post_with_group, self.post_with_group)
        self.assertEqual(post_without_group, self.post_without_group)
        self.assertEqual(post_with_image, self.post_with_image)
        self.assertIsInstance(post_with_image.image, ImageFieldFile)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.posts = (
            Post(
                author=cls.user,
                text=f'Тестовый пост под номером {post_number}',
                group=cls.group,
            )
            for post_number in range(13)
        )
        cls.post_list = Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_correct_posts_amount(self):
        urls = (
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            ),
        )
        posts_on_second_page = Post.objects.count() % POSTS_AMOUNT
        for url in urls:
            with self.subTest(url=url):
                response_first_page = self.authorized_client.get(url)
                response_second_page = self.authorized_client.get(
                    url, {'page': 2},
                )
                self.assertEqual(
                    len(response_first_page.context['page_obj']), POSTS_AMOUNT
                )
                self.assertEqual(
                    len(response_second_page.context['page_obj']),
                    posts_on_second_page
                )
