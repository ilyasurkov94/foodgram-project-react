from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER = 'user'
    ADMIN = 'admin'
    BLOCKED = 'blocked'
    ROLE_CHOICES = (
        (USER, USER),
        (ADMIN, ADMIN),
        (BLOCKED, BLOCKED)
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Почта Email',
        help_text='Укажите email',
        error_messages={
            'unique': ('Такой email уже зарегистрирован'),
        }
    )
    username = models.CharField(
        max_length=500,
        unique=True,
        verbose_name='Юзернейм',
        help_text='Укажите Username',
        error_messages={
            'unique': ('Такой Username занят'),
        }
    )
    first_name = models.CharField(
        max_length=500,
        verbose_name='Имя',
        help_text='Укажите имя',
    )
    last_name = models.CharField(
        max_length=500,
        verbose_name='Фамилия',
        help_text='Укажите фамилию',
    )
    role = models.CharField(
        choices=ROLE_CHOICES,
        max_length=500,
        default=USER,
        verbose_name='Пользовательские роли',
    )

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    @property
    def is_user(self):
        return self.role == self.USER

    @property
    def is_blocked(self):
        return self.role == self.BLOCKED

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return (f'{self.username}, id - {self.id}. '
                f'{self.first_name} {self.last_name}')
