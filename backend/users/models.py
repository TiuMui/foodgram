from django.contrib.auth.models import AbstractUser
from django.db import models

from core.validators import validate_username


class CustomUser(AbstractUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Адрес электронной почты',
        error_messages={
            'unique': 'Этот адрес электронной почты уже используется.'
        }
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Уникальное имя пользователя',
        validators=(validate_username,),
        error_messages={
            'unique': 'Это имя пользователя уже занято.'
        }
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='subscriptions'
    )
    subscription = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Подписка',
        related_name='subscribers'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'subscription'],
                name='unique_subscriber_subscription',
                violation_error_message='Подписка уже оформлена.'
            ),
            models.CheckConstraint(
                check=~models.Q(subscriber=models.F('subscription')),
                name='no_self_subscribed'
            )
        ]

    def __str__(self):
        return f'{self.subscriber.username} >>> {self.subscription.username}'
