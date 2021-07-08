from django.test import TestCase

from ..models import Post, Group, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )

    def test_text_show(self):
        post = PostModelTest.post
        test_text = str(post)
        true_text = post.text[:15]
        self.assertEqual(test_text, true_text)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый title',
            slug='test'
        )

    def test_title_show(self):
        group = GroupModelTest.group
        test_title = str(group)
        true_title = group.title
        self.assertEqual(test_title, true_title)
