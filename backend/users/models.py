from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings

username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Имя пользователя содержит недопустимые символы.',
)


class User(AbstractUser):
    """Кастомная модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        'Адрес электронной почты',
        max_length=254,
        unique=True,
        help_text='Укажите ваш адрес электронной почты.'
    )
    username = models.CharField(
        'Уникальный юзернейм',
        max_length=150,
        unique=True,
        help_text=(
            'Укажите ваш юзернейм (никнейм). Допустимые символы: '
            'буквы, цифры и @/./+/-/_'
        ),
        validators=[username_validator],
        error_messages={
            'unique': "Пользователь с таким юзернеймом уже существует.",
        },
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
        help_text='Укажите ваше имя.'
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
        help_text='Укажите вашу фамилию.'
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/avatars/',
        blank=True,
        null=True,
        help_text='Загрузите ваш аватар'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки пользователя на автора."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
    created = models.DateTimeField(
        'Дата подписки',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
