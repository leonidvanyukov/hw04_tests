from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description'
        )
        cls.form_data = {
            'text': 'test-post',
            'group': cls.group.id,
        }
        cls.post = Post.objects.create(
            text=PostFormTests.form_data['text'],
            author=PostFormTests.user,
            group=PostFormTests.group,
        )

    def test_create_post(self):
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=PostFormTests.form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args={PostFormTests.user}),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group.id,
                text=PostFormTests.form_data['text'],
                id=PostFormTests.post.id + 1,
            ).exists()
        )

    def test_edit_post(self):
        PostFormTests.form_data['text'] = 'test-post1'
        response = self.authorized_client.post(
            reverse('posts:post_edit', args={PostFormTests.post.id}),
            data=PostFormTests.form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args={PostFormTests.post.id}),
        )
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group.id,
                text=PostFormTests.form_data['text'],
                id=PostFormTests.post.id,
            ).exists(),
        )
