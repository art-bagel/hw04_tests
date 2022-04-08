from django.shortcuts import render


def page_not_found(request, exception):
    """Выводит кастомную страницу 404 ошибки."""
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def server_error(request):
    """Выдает кастомную страницу 500 ошибки.
    Если возникли проблемы на сревере.
    """
    return render(request, 'core/500.html', status=500)


def permission_denied(request, exception):
    """Выдает кастомную страницу 403 ошибки, если доступ к запрашиваемой
    странице запрешен.
    """
    return render(request, 'core/403.html', status=403)


def csrf_failure(request, reason=''):
    """Выдает кастомную страницу ошибки 403 если форма не вернула корректный
    csrf токен.
    """
    return render(request, 'core/403csrf.html')
