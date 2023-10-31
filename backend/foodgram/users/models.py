from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


REGEX = r'^[\w.@+-_]'


class User(AbstractUser):
    "Модель пользователя"
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[RegexValidator(regex=REGEX)]
    )
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=150)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username', 'first_name', 'last_name', 'password'
    )

    def __str__(self):
        return self.username
