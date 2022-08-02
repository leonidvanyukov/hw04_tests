from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Изображение',
        }
        help_texts = {
            'text': 'Введите текст Вашего нового поста',
            'group': 'Выберете группу Вашего нового поста',
            'image': 'Загрузите изображение для Вашего нового поста',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {
            'text': 'Комментарий',
        }
        help_texts = {
            'text': 'Введите текст Вашего комментария',
        }
