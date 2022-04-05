from django.forms import ModelForm, Textarea
from django.utils.translation import gettext_lazy

from posts.models import Post


class PostForm(ModelForm):
    """Форма для создания и редактирования постов."""
    class Meta:
        model = Post
        fields = ('text', 'group')
        widgets = {
            'text': Textarea(attrs={'cols': 80, 'rows': 10}),
        }
        labels = {
            'text': gettext_lazy('Текст поста'),
            'group': gettext_lazy('Выберите группу')
        }
        help_texts = {
            'text': gettext_lazy('Текст нового поста'),
            'group': gettext_lazy('Группа, к которой будет относиться пост')
        }
