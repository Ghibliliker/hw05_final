from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': _('Пост'),
            'group': _('Имя группы'),
            'image': _('Картиночка'),
        }
        help_texts = {
            'text': _('Поле для ввода содержимого поста.'),
            'group': _('Выбрать группу, где будет запощен пост'),
            'image': _('Загрузите картиночку'),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {
            'text': _('Текст'),
        }
        help_text = {
            'text': _('Поле ввода комментария'),
        }
