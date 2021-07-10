from django.db import models
from django.db.models import Q, F
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts', blank=True, null=True
    )
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField()
    created = models.DateTimeField('date published', auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        ordering = ['-user']
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='user_author_unique'
            ),
            # здесь шла какая-то непонятная ошибка при миграции
            # наставник сказал добавить ~ перед Q и все заработало
            # может скинете что-нибудь про Q и F с адекватными понятными
            # примерами, ибо сделал я методом тыка,
            # несовсем понимая, что логически происходит
            # примеров найти не удалось, везде пример с возрастом :(
            models.CheckConstraint(
                check=~Q(user=F('author')),
                name='not_yourself_following'
            )
        ]
