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
        self.guest_client = Client()
        self.user = PostUrlTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user = User.objects.create_user(username='NotAuthor')
        self.not_author_client = Client()
        self.not_author_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/profile.html': '/profile/test-user/',
            'posts/post_detail.html': '/posts/1/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'response = {response}, template = {template}'
                )

    def test_404_status_code(self):
        """Несуществующий URL-адрес выдает 404"""
        response = self.guest_client.get('/404/')
        self.assertEqual(response.status_code, 404)

    def test_posts_create_url_uses_correct_template(self):
        """Страница /create/ использует шаблон posts/new_post.html"""
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/new_post.html')
        response = self.guest_client.get('/create/')
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_posts_edit_url_uses_correct_template(self):
        """
        Страница /posts/<post_id>/edit/ использует шаблон posts/new_post.html
        """
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/new_post.html')
        response = self.guest_client.get('/posts/1/edit/')
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/'
        )
        response = self.not_author_client.get('/posts/1/edit/')
        self.assertRedirects(
            response, '/profile/NotAuthor/'
        )
