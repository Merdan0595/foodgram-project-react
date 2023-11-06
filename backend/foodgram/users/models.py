from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

from recipes.constants import REGEX


class User(AbstractUser):
    "Модель пользователя"
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[RegexValidator(regex=REGEX)],
        verbose_name='Имя пользователя'
    )
    email = models.EmailField(max_length=254, unique=True,
                              verbose_name='Электронная почта')
    first_name = models.CharField(max_length=150,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=150,
                                 verbose_name='Фамилия')
    password = models.CharField(max_length=150,
                                verbose_name='Пароль')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username', 'first_name', 'last_name', 'password'
    )

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
