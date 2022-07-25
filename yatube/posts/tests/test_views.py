from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

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
        for i in range(1, 14):
            cls.post = Post.objects.create(
                author=cls.user,
                text='test-text',
            )

    def setUp(self):
        self.guest_client = Client()
        self.user = PostViewTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """Nampespace:name использует соответствующий шаблон"""

        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/new_post.html': reverse('posts:post_create'),
            'posts/group_list.html': (reverse('posts:group', kwargs={'slug': 'test-slug'})),
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
        post_author_0 = first_object.author.username
        self.assertEqual(post_text_0, 'test-text')
        self.assertEqual(post_author_0, 'test-user')

    def test_group_page_show_correct_context(self):
        """Пост отображается на странице группы"""

        response = self.authorized_client.get(
            reverse('posts:group', args={'test-slug'}))
        post_group_title = response.context['group']
        self.assertEqual(post_group_title.title, 'test-title')

    def test_first_page_contains_ten_records(self):
        """Количество постов на первой странице равно 10"""

        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page_obj').object_list), 10)

    def test_second_page_contains_three_records(self):
        """Количество постов на второй странице равно 3"""

        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context.get('page_obj').object_list), 3)
