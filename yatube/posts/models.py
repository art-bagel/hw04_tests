from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField(verbose_name='Контент',
                            help_text='Текст для нового поста'
                            )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name='Автор'
                               )
    group = models.ForeignKey(Group,
                              blank=True,
                              null=True,
                              on_delete=models.SET_NULL,
                              related_name='posts',
                              verbose_name='Группа',
                              help_text='Группа, к которой относиться пост'
                              )
    image = models.ImageField(verbose_name='Картинка',
                              upload_to='posts/',
                              blank=True,
                              help_text='Выберите картинку к посту'
                              )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return str(self.text[:15])


class Comment(CreatedModel):
    text = models.TextField(verbose_name='Ваш комментарий')
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments'
                             )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments'
                               )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower'
                             )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following'
                               )

    class Meta:
        unique_together = ['user', 'author']
        constraints = [
            models.CheckConstraint(check=(~models.Q(user=models.F('author'))),
                                   name='author_and_user_are_different'),
        ]
