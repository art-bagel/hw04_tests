from django.forms import ModelForm, Textarea

from posts.models import Comment, Post


class PostForm(ModelForm):
    """Форма для создания и редактирования постов."""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        widgets = {
            'text': Textarea(attrs={'cols': 80, 'rows': 10}),
        }


class CommentForm(ModelForm):
    """Форма для создания комментария к посту."""
    class Meta:
        model = Comment
        fields = ('text', )
        widgets = {
            'text': Textarea(attrs={'cols': 80, 'rows': 5})
        }
