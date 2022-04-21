from django.db import models


class CreatedModel(models.Model):
    """Абстрактная модель. Добавляет дату создания."""
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата создания'
                                   )

    class Meta:
        abstract = True
