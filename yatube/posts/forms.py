from django import forms
from django.core.exceptions import ValidationError

from .models import Comment, Post

MIN_TEXT_LENGTH = 8


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = (
            'text', 'group', 'image',
        )

    def clean_text(self):
        text = self.cleaned_data['text']
        if len(text) < MIN_TEXT_LENGTH:
            raise ValidationError(
                'Текст поста слишком короткий'
            )
        return text


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            'text',
        )

    def clean_text(self):
        text = self.cleaned_data['text']
        if len(text) < MIN_TEXT_LENGTH:
            raise ValidationError(
                'Комментарий слишком короткий'
            )
        return text
