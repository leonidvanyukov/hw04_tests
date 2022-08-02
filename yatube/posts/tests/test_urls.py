from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test-post',
        )

    def setUp(self):
        self.user = PostUrlTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.not_author_user = User.objects.create_user(username='NotAuthor')
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author_user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'response = {response}, template = {template}'
                )

    def test_404_status_code(self):
        """Несуществующий URL-адрес выдает 404"""
        response = self.client.get('/404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_posts_create_url_uses_correct_template(self):
        """Страница /create/ использует шаблон posts/new_post.html"""
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/new_post.html')
        response = self.client.get('/create/')
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_posts_edit_url_uses_correct_template(self):
        """
        Страница /posts/<post_id>/edit/ использует шаблон posts/new_post.html
        """
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/new_post.html')
        response = self.client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )
        response = self.not_author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(
            response, f'/profile/{self.not_author_user.username}/'
        )

    def test_pages_available(self):
        """Все страницы доступны"""
        url_names = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user}/',
            f'/posts/{self.post.id}/',
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
