from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.another_author = User.objects.create_user(username='AnotherUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст, длиной более чем 15 символов',
        )
        cls.another_author_post = Post.objects.create(
            author=cls.another_author,
            text='Тестовый текст совершенно другого человека',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exist_at_desired_location(self):
        """Страницы приложения posts доступны по ожидаемому адресу"""
        public_urls = (
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            ),
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk},
            ),
        )
        for url in public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK
                )

    def test_post_operation_urls_exist_at_desired_location(self):
        post_operations_urls = (
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            ),
        )
        for url in post_operations_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK
                )

    def test_non_existent_page_is_not_found(self):
        response = self.guest_client.get('nonexistent_page/')
        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND
        )

    def test_urls_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        template_url_names = {
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug},
            ): 'posts/group_list.html',
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk},
            ): 'posts/post_detail.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            ): 'posts/profile.html',
        }
        for address, template in template_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_non_existent_page_correct_template(self):
        template = 'core/404.html'
        response = self.guest_client.get('nonexistent_page/')
        self.assertTemplateUsed(response, template)

    def test_post_operation_urls_redirect_guest_on_login(self):
        """Редирект неавторизованного пользователя на страницу входа
        при попытке создать или изменить пост
        """
        authorized_urls = (
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            ),
        )
        for url in authorized_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                login_url = reverse('users:login')
                target_url = f'{login_url}?next={url}'
                self.assertRedirects(
                    response, target_url
                )

    def test_post_edit_url_redirect_user_on_post_page(self):
        """Редирект авторизованного пользователя на страницу с постом
        при попытке изменить не свой пост
        """
        post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.another_author_post.pk},
        )
        post_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.another_author_post.pk},
        )
        response = self.authorized_client.get(post_edit_url, follow=True)
        self.assertRedirects(
            response, post_url
        )
