import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post
from ..utils import count_elements

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
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
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description',
        )
        cls.post = Post.objects.create(
                author=cls.user,
                text='test-text',
                image=cls.uploaded,
                group=cls.group
        )
        cls.second_group = Group.objects.create(
            title='second-title',
            slug='second-slug',
            description='second-description',
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }

    def setUp(self):
        self.user = PostViewTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
            'image': forms.fields.ImageField,
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

    def post_test(self, response_post):
        """Функция для тестирования контекста поста на странице"""
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image = response_post.image
        self.assertEqual(post_author, PostViewTest.user)
        self.assertEqual(post_group, PostViewTest.group)
        self.assertEqual(post_text, PostViewTest.post.text)
        self.assertEqual(post_image, PostViewTest.post.image)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:index'))
        response_post = response.context.get('page_obj')[0]
        self.post_test(response_post)

    def test_index_show_correct_profile(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', args={PostViewTest.user})
        )
        author = PostViewTest.user
        response_author = response.context.get('author')
        response_count = response.context.get('posts_count')
        response_post = response.context.get('page_obj').object_list[0]
        self.post_test(response_post)
        self.assertEqual(author, response_author)
        self.assertEqual(1, response_count)

    def test_index_show_correct_post_view(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.client.get(
            reverse(
                'posts:post_detail',
                args={PostViewTest.post.id}
            )
        )
        response_post = response.context.get('post')
        response_count = response.context.get('posts_count')
        self.post_test(response_post)
        self.assertEqual(1, response_count)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                args={PostViewTest.post.id}
            )
        )
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_group_slug_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group', args=[PostViewTest.group.slug])
        )
        response_post = response.context.get('page_obj').object_list[0]
        self.post_test(response_post)


class PaginatorViewTest(TestCase):
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
                group=cls.group
            )

    def test_first_page_contains_ten_records(self):
        """Количество постов на первой странице равно 10"""

        response = self.client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context.get('page_obj').object_list),
            settings.AMOUNT
        )

    def test_second_page_contains_three_records(self):
        """Пагинатор второй страницы выдает нужно количество постов"""

        author = get_object_or_404(User, username=self.post.author.username)
        author_posts = author.posts.all()
        posts_count_left = count_elements(author_posts) - settings.AMOUNT
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context.get('page_obj').object_list),
            posts_count_left
        )


class CommentViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test-auth-user'
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author = User.objects.create_user(
            username='test-author'
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description'
        )

        cls.post = Post.objects.create(
            text='test-post',
            group=cls.group,
            author=cls.author
        )

    def test_add_comment_for_guest(self):
        response = self.client.get(
            reverse(
                'posts:add_comment',
                args={CommentViewTest.post.id}
            )
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            ('Не авторизированный пользователь'
             ' не может оставлять комментарий')
        )

    def test_comment_for_auth_user(self):
        """Авторизированный пользователь может оставить комментарий"""
        client = self.authorized_client
        post = CommentViewTest.post
        response = client.get(
            reverse(
                'posts:add_comment',
                args={post.id}
            )
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            ('Авторизированный пользователь'
             ' должен иметь возможность'
             ' оставлять комментарий')
        )
        comments_count = Comment.objects.filter(
            post=post.pk
        ).count()
        form_data = {
            'text': 'test-comment',
        }

        response = client.post(
            reverse('posts:add_comment',
                    args={post.id}
                    ),
            data=form_data,
            follow=True
        )
        comments = Post.objects.filter(
            id=post.pk
        ).values_list('comments', flat=True)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                args={post.id}
            )
        )
        self.assertEqual(
            comments.count(),
            comments_count + 1
        )
        self.assertTrue(
            Comment.objects.filter(
                post=post.pk,
                author=CommentViewTest.user.id,
                text=form_data['text']
            ).exists()
        )


class CacheViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description'
        )
        cls.post = Post.objects.create(
            text='test-post',
            group=cls.group,
            author=cls.author
        )

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = CacheViewTest.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test-new-post',
            author=CacheViewTest.author,
        )
        response_old = CacheViewTest.authorized_client.get(
            reverse('posts:index')
        )
        old_posts = response_old.content
        self.assertEqual(
            old_posts,
            posts,
            'Не возвращает кэшированную страницу.'
        )
        cache.clear()
        response_new = CacheViewTest.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts, 'Нет сброса кэша.')


class FollowViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='test-author'
        )
        cls.auth_author_client = Client()
        cls.auth_author_client.force_login(cls.author)

        cls.user_fol = User.objects.create_user(
            username='test-user-fol'
        )
        cls.authorized_user_fol_client = Client()
        cls.authorized_user_fol_client.force_login(
            cls.user_fol
        )

        cls.user_unfol = User.objects.create_user(
            username='test-user-unfol'
        )
        cls.authorized_user_unfol_client = Client()
        cls.authorized_user_unfol_client.force_login(
            cls.user_unfol
        )
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description'
        )
        cls.post = Post.objects.create(
            text='test-post',
            group=cls.group,
            author=cls.author
        )

    def test_follow(self):
        """Тест работы подписки на автора."""
        client = FollowViewTest.authorized_user_unfol_client
        user = FollowViewTest.user_unfol
        author = FollowViewTest.author
        client.get(
            reverse(
                'posts:profile_follow',
                args=[author.username]
            )
        )
        follower = Follow.objects.filter(
            user=user,
            author=author
        ).exists()
        self.assertTrue(
            follower,
            'Не работает подписка на автора'
        )

    def test_unfollow(self):
        """Тест работы отписки от автора."""
        client = FollowViewTest.authorized_user_unfol_client
        user = FollowViewTest.user_unfol
        author = FollowViewTest.author
        client.get(
            reverse(
                'posts:profile_unfollow',
                args=[author.username]
            ),

        )
        follower = Follow.objects.filter(
            user=user,
            author=author
        ).exists()
        self.assertFalse(
            follower,
            'Не работает отписка от автора'
        )

    def test_new_author_post_for_follower(self):
        client = FollowViewTest.authorized_user_fol_client
        author = FollowViewTest.author
        group = FollowViewTest.group
        client.get(
            reverse(
                'posts:profile_follow',
                args=[author.username]
            )
        )
        response_old = client.get(
            reverse('posts:follow_index')
        )
        old_posts = response_old.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page_obj').object_list),
            1,
            'Не загружается правильное количество старых постов'
        )
        self.assertIn(
            FollowViewTest.post,
            old_posts,
            'Старый пост не верен'
        )
        new_post = Post.objects.create(
            text='test-new-post',
            group=group,
            author=author
        )
        cache.clear()
        response_new = client.get(
            reverse('posts:follow_index')
        )
        new_posts = response_new.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page_obj').object_list),
            2,
            'Нет нового поста'
        )
        self.assertIn(
            new_post,
            new_posts,
            'Новый пост неверен'
        )

    def test_new_author_post_for_unfollower(self):
        client = FollowViewTest.authorized_user_unfol_client
        author = FollowViewTest.author
        group = FollowViewTest.group
        response_old = client.get(
            reverse('posts:follow_index')
        )
        old_posts = response_old.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page_obj').object_list),
            0,
            'Не загружается правильное количество старых постов'
        )
        self.assertNotIn(
            FollowViewTest.post,
            old_posts,
            'Старый пост не должен загружаться'
        )
        new_post = Post.objects.create(
            text='test-new-post',
            group=group,
            author=author
        )
        cache.clear()
        response_new = client.get(
            reverse('posts:follow_index')
        )
        new_posts = response_new.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page_obj').object_list),
            0,
            'Новый пост не должен появляться'
        )
        self.assertNotIn(
            new_post,
            new_posts,
            'Новый пост не должен появляться'
        )
