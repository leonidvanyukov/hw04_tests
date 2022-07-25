from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='test-user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description'
        )

    def test_create_post(self):
        posts_count = Post.objects.count()
        group_field = PostFormTests.group.id
        form_data = {
            'text': 'test-post',
            'group': group_field,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args={PostFormTests.user}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group.id,
                text='test-post'
            ).exists()
        )
        form_data = {
            'text': 'test-post1',
            'group': group_field,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args={1}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args={'1'}
        ))
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group.id,
                text='test-post1'
            ).exists()
        )
