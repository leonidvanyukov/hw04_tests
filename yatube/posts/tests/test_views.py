from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings
from django.shortcuts import get_object_or_404

from ..utils import count_elements
from ..models import Group, Post

User = get_user_model()


class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description',
        )
        for _ in range(1, 14):
            cls.post = Post.objects.create(
                author=cls.user,
                text='test-text',
            )
        cls.second_group = Group.objects.create(
            title='second-title',
            slug='second-slug',
            description='second-description',
        )

    def setUp(self):
        self.user = PostViewTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """Nampespace:name использует соответствующий шаблон"""
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/new_post.html': reverse('posts:post_create'),
            'posts/group_list.html': (reverse(
                'posts:group',
                kwargs={'slug': self.group.slug}
            )),
        }

        for template, reverse_name in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_new_post_page_show_correct_context(self):
        """Форма добавления материала сформирована с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context['form'].fields[value]
                self.assertIsInstance(form_fields, expected)

    def test_home_page_show_correct_context(self):
        """Пост отображается на главной странице"""

        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_id_0 = first_object.id
        self.assertTrue(
            Post.objects.filter(
                group=post_group_0,
                text=post_text_0,
                id=post_id_0,
            ).exists(),
        )

    def test_group_page_show_correct_context(self):
        """Пост отображается на странице группы"""

        response = self.authorized_client.get(
            reverse('posts:group', args={self.group.slug}))
        post_group_title = response.context['group']
        self.assertEqual(post_group_title.title, self.group.title)

    def test_profile_page_show_correct_context(self):
        """Пост отображается на странице профиля"""

        response = self.authorized_client.get(
            reverse('posts:profile', args={self.post.author.username}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author.username)

    def test_post_not_in_wrong_group(self):
        """Пост не отображается в чужой группе"""

        response = self.authorized_client.get(
            reverse('posts:group', args={self.second_group.slug}))
        post_second_group_title = response.context['group']
        self.assertNotEqual(post_second_group_title.title, self.group.title)

    def test_first_page_contains_ten_records(self):
        """Количество постов на первой странице равно 10"""

        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page_obj').object_list), settings.AMOUNT)

    def test_second_page_contains_three_records(self):
        """Количество постов на второй странице равно 3"""

        author = get_object_or_404(User, username=self.post.author.username)
        author_posts = author.posts.all()
        posts_count_left = count_elements(author_posts) - settings.AMOUNT
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context.get('page_obj').object_list), posts_count_left)
