import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls.base import reverse
from django import forms
from django.conf import settings

from ..models import Comment, Post, Group, Follow, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовый title',
            slug='test',
            description='описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        cls.templates = {
            'index.html': reverse('index'),
            'group.html': reverse(
                'group_posts',
                kwargs={'slug': f'{cls.group.slug}'}
            ),
            'new.html': reverse('new_post'),
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()
        cache.clear()

    def check_context_of_create_post(self, response):
        create_post = response.context.get('page')[0]
        self.assertEqual(create_post.text, self.post.text)
        self.assertEqual(create_post.author, self.post.author)
        self.assertEqual(create_post.group, self.post.group)
        self.assertEqual(create_post.pub_date, self.post.pub_date)
        self.assertEqual(create_post.image, self.post.image)
        self.assertIn(self.post, response.context.get('page'))

    def test_anon_not_add_comment(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст'
        }
        self.guest_client.post(
            reverse(
                'add_comment',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id
                }
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_user_add_comment(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст'
        }
        self.authorized_client.post(
            reverse(
                'add_comment',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id
                }
            ),
            data=form_data,
            follow=True
        )
        post_comment = Comment.objects.get(pk=1)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(post_comment.text, form_data['text'])
        self.assertEqual(post_comment.author, self.user)
        self.assertEqual(post_comment.post.id, self.post.id)

    def test_cache_exists(self):
        response1 = self.authorized_client.get(reverse('index'))
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.user
        )
        response2 = self.authorized_client.get(reverse('index'))
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response3 = self.authorized_client.get(reverse('index'))
        self.assertNotEqual(response2.content, response3.content)
        self.assertIn(post, response3.context['page'])

    def test_templates_use_correct(self):
        for template, name in self.templates.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                self.assertTemplateUsed(response, template)

    def test_context_use_index(self):
        response = self.authorized_client.get(reverse('index'))
        self.check_context_of_create_post(response)

    def test_context_use_group(self):
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': f'{self.group.slug}'})
        )
        context_group = response.context.get('group')
        self.assertEqual(context_group.title, self.group.title)
        self.assertEqual(context_group.slug, self.group.slug)
        self.check_context_of_create_post(response)

    def test_context_use_new(self):
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_context_use_edit(self):
        response = self.authorized_client.get(
            reverse(
                'post_edit',
                kwargs={
                    'username': f'{self.user.username}',
                    'post_id': f'{self.post.id}'
                }
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_context_use_profile(self):
        response = self.authorized_client.get(
            reverse(
                'profile',
                kwargs={'username': f'{self.user.username}'}
            )
        )
        self.assertEqual(
            response.context['author'].username,
            self.user.username
        )
        self.check_context_of_create_post(response)

    def test_context_use_post(self):
        response = self.authorized_client.get(
            reverse(
                'post_view',
                kwargs={
                    'username': f'{self.user.username}',
                    'post_id': f'{self.post.id}'
                }
            )
        )
        context = response.context['post']
        self.assertEqual(context.text, f'{self.post.text}')
        self.assertEqual(context.author.username, f'{self.post.author}')
        self.assertEqual(context.image, f'{self.post.image}')
        self.assertEqual(context.group.title, f'{self.post.group}')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user_p')
        cls.group = Group.objects.create(
            title='Тестовый title',
            slug='test',
            description='описание'
        )
        for i in range(13):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.user,
                group=cls.group
            )
        cls.url_names = [
            reverse('index'),
            reverse('group_posts', kwargs={'slug': f'{cls.group.slug}'})
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        for adress in self.url_names:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                i = response.context.get('page')
                self.assertEqual(len(i.object_list), 10)

    def test_second_page_contains_three_records(self):
        for adress in self.url_names:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress + '?page=2')
                i = response.context.get('page')
                self.assertEqual(len(i.object_list), 3)


class CreateViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user2 = User.objects.create_user(username='test_user2')
        cls.user3 = User.objects.create_user(username='test_user3')
        cls.user4 = User.objects.create_user(username='test_user4')
        cls.group = Group.objects.create(
            title='Тестовый title',
            slug='test',
            description='описание'
        )
        cls.group1 = Group.objects.create(
            title='Тестовый title1',
            slug='test1',
            description='описание1'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )
        cls.post2 = Post.objects.create(
            text='Тестовый текст2',
            author=cls.user2,
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        self.authorized_client3 = Client()
        self.authorized_client3.force_login(self.user3)

    def test_follow_post_exists(self):
        response = self.authorized_client3.get(
            reverse(
                'profile_follow', kwargs={'username': f'{self.user.username}'}
            )
        )
        response = self.authorized_client3.get(reverse('follow_index'))
        self.assertIn(self.post, response.context['page'])

    def test_follow_post_not_exists(self):
        response = self.authorized_client3.get(
            reverse(
                'profile_follow', kwargs={'username': f'{self.user.username}'}
            )
        )
        response = self.authorized_client3.get(reverse('follow_index'))
        self.assertNotIn(self.post2, response.context['page'])

    def test_unfollow_author(self):
        Follow.objects.create(user=self.user2, author=self.user)
        follow_count = Follow.objects.count()
        self.authorized_client2.get(
            reverse(
                'profile_unfollow', kwargs={
                    'username': f'{self.user.username}'
                }
            )
        )
        self.assertFalse(
            Follow.objects.filter(author=self.user, user=self.user2).exists()
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_follow_author(self):
        follow_count = Follow.objects.count()
        self.authorized_client2.get(
            reverse(
                'profile_follow', kwargs={'username': f'{self.user.username}'}
            )
        )
        self.assertTrue(
            Follow.objects.filter(author=self.user, user=self.user2).exists()
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_group_notcontains_post(self):
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': f'{self.group1.slug}'})
        )
        self.assertNotIn(self.post, response.context.get('page'))

    def test_index_contains_post(self):
        response = self.authorized_client.get(reverse('index'))
        self.assertIn(self.post, response.context['page'])

    def test_group_contains_post(self):
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': f'{self.group.slug}'})
        )
        self.assertIn(self.post, response.context['page'])
