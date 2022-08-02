import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description'
        )
        cls.form_data = {
            'text': 'test-post',
            'group': cls.group.id,
            'image': cls.uploaded,
        }
        cls.post = Post.objects.create(
            text=cls.form_data['text'],
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
        small_gif_new = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded_new = SimpleUploadedFile(
            name='small_new.gif',
            content=small_gif_new,
            content_type='image/gif'
        )
        PostFormTests.form_data['image'] = uploaded_new
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
