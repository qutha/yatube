from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.deletion import CASCADE
from django.db.models.deletion import SET_NULL

User = get_user_model()
POST_MAX_LENGTH_NAME = 15


class Group(models.Model):
    objects = models.Manager()
    title = models.CharField('Название', max_length=200)
    slug = models.SlugField('Слаг', unique=True)
    description = models.TextField('Описание')

    def __str__(self):
        return self.title


class Post(models.Model):
    objects = models.Manager()
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста',
    )
    author = models.ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Выберите группу',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )
    created = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.text[:POST_MAX_LENGTH_NAME]


class Comment(models.Model):
    objects = models.Manager()
    post = models.ForeignKey(
        Post,
        on_delete=CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        'Комментарий',
        help_text='Поделитесь своей мыслью',
    )
    created = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        ordering = ['-created']


class Follow(models.Model):
    objects = models.Manager()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )
