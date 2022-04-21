from typing import Tuple

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from posts.forms import PostForm, CommentForm
from posts.models import Group, Post, Follow
from posts.services import get_paginator

User = get_user_model()


@cache_page(20)
def index(request: HttpRequest) -> HttpResponse:
    """Возвращает главную страницу сайта со всеми постами."""
    post_list = Post.objects.select_related('author', 'group')
    page_obj = get_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request: HttpRequest, slug: str) -> HttpResponse:
    """Возвращает страницу с постами для выбранной группы."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    page_obj = get_paginator(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request: HttpRequest, username: str) -> HttpResponse:
    """Возвращает страницу автора, его посты и ссылки на группы,
    к которым они относятся.
    """
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group')
    page_obj = get_paginator(request, post_list)
    following = request.user.is_authenticated and author.following.filter(
        user_id=request.user.id).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    """Возвращает страницу с подробной информацией о посте."""
    post = get_object_or_404(Post.objects.select_related('group'), id=post_id)
    number_posts_author = Post.objects.filter(author=post.author).count()
    comments = post.comments.select_related('author')
    comments_form = CommentForm()
    context = {
        'post': post,
        'number_posts_author': number_posts_author,
        'comments': comments,
        'form': comments_form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required()
def post_create(request: HttpRequest) -> HttpResponse:
    """Возвращает страницу c формой создания поста."""
    if request.method != 'POST':
        form = PostForm()
        return render(request, 'posts/create_post.html',
                      context={'form': form})
    form = PostForm(request.POST, files=request.FILES)
    if not form.is_valid():
        return render(request, 'posts/create_post.html',
                      context={'form': form})
    new_post = form.save(commit=False)
    new_post.author_id = request.user.id
    new_post.save()
    return redirect('posts:profile', username=request.user.username)


@login_required()
def post_edit(request: HttpRequest, post_id: int) -> HttpResponse:
    """Возвращает страницу c формой редактирования выбранного поста."""
    post = get_object_or_404(Post, id=post_id)
    if request.user.id != post.author_id:
        raise PermissionDenied()
    if request.method != 'POST':
        form = PostForm(instance=post)
        return render(request, 'posts/create_post.html',
                      context={'form': form, 'is_edit': True})
    form = PostForm(request.POST, files=request.FILES, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/create_post.html',
                  context={'form': form, 'is_edit': True})


@login_required()
def add_comment(request: HttpRequest, post_id: int) -> HttpResponse:
    """Добавление комментария к посту."""
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request: HttpRequest) -> HttpResponse:
    """Возвращает страницу с постами авторов, на которых подписан
    пользователь.
    """
    authors_id = Follow.objects.filter(
        user_id=request.user.id).values('author_id')
    post_list = Post.objects.filter(
        author__in=authors_id).select_related('author', 'group')
    page_obj = get_paginator(request, post_list)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request: HttpRequest, username: str) -> HttpResponse:
    """Добавление подписки на автора."""
    author, user, following = _get_follow_info(request, username)
    author.following.create(user_id=user.id)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request: HttpRequest, username: str) -> HttpResponse:
    """Удаление автора из пописок."""
    _, _, following = _get_follow_info(request, username)
    following.delete()
    return redirect('posts:follow_index')


def _get_follow_info(request: HttpRequest,
                     username: str
                     ) -> Tuple[User, User, QuerySet]:
    """Возвращает словарь с автором, пользователем и его подписками."""
    author = get_object_or_404(User, username=username)
    user = request.user
    following = author.following.filter(user_id=user.id)
    return author, user, following
