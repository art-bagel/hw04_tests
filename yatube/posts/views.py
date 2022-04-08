from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from posts.forms import PostForm
from posts.models import Group, Post
from posts.services import get_paginator

User = get_user_model()


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
    context = {
        'author': author,
        'page_obj': page_obj
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    """Возвращает страницу с подробной информацией о посте."""
    post = get_object_or_404(Post, id=post_id)
    number_posts_author = Post.objects.filter(author=post.author).count()
    context = {
        'post': post,
        'number_posts_author': number_posts_author
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
        return redirect('posts:post_detail', post_id=post_id)
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
