from django.core.paginator import Page, Paginator
from django.db.models import QuerySet
from django.http import HttpRequest

from yatube.settings import POSTS_PER_PAGE


def get_paginator(request: HttpRequest, post_list: QuerySet) -> Page:
    """Возвращает Paginator."""
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
