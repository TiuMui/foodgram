import hashlib

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.constants import (
    MAX_COOCKING_TIME,
    MAX_INGREDIENT_AMOUNT,
    MAX_LENGTH_DEFAULT,
    MAX_LENGTH_INGREDIENT_NAME,
    MAX_LENGTH_INGREDIENT_UNIT,
    MAX_LENGTH_RECIPE_NAME,
    MAX_LENGTH_SHORT_HASH,
    MIN_COOCKING_TIME,
    MIN_INGREDIENT_AMOUNT,
)

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_INGREDIENT_NAME,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_INGREDIENT_UNIT,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name-measurement_unit',
                violation_error_message='Такой ингредиент уже есть.'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='ingredients_in_recipe'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        default=MIN_INGREDIENT_AMOUNT,
        verbose_name='Количество ингредиента',
        validators=(
            MaxValueValidator(
                MAX_INGREDIENT_AMOUNT,
                message=f'Должно быть не больше {MAX_INGREDIENT_AMOUNT}'
            ),
            MinValueValidator(
                MIN_INGREDIENT_AMOUNT,
                message=f'Должно быть не меньше {MIN_INGREDIENT_AMOUNT}'
            )
        )
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        ordering = ('ingredient',)
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe-ingredient',
                violation_error_message='Ингредиент уже в рецепте.'
            )
        ]

    def __str__(self):
        return f'Ингредиент в рецепте {self.recipe.name}'


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_DEFAULT,
        unique=True,
        verbose_name='Уникальное название тега'
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_DEFAULT,
        unique=True,
        verbose_name='Уникальный слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='author_recipes'
    )
    name = models.CharField(
        max_length=MAX_LENGTH_RECIPE_NAME,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение готового блюда',
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through=IngredientInRecipe,
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='tag_recipes'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=(
            MaxValueValidator(
                MAX_COOCKING_TIME,
                message=f'Должно быть не больше {MAX_COOCKING_TIME}'
            ),
            MinValueValidator(
                MIN_COOCKING_TIME,
                message=f'Должно быть не меньше {MIN_COOCKING_TIME}'
            )
        )
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    short_hash = models.CharField(
        verbose_name='Уникальная строка',
        max_length=MAX_LENGTH_SHORT_HASH,
        blank=True,
        null=True,
        unique=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def save(self, *args, **kwargs):
        if not self.short_hash:
            unique_string = f'{self.id}-{self.name}-{self.text}'
            hash_object = hashlib.sha256(unique_string.encode())
            self.short_hash = hash_object.hexdigest()[:MAX_LENGTH_SHORT_HASH]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """Класс модели для Избранного."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт в избранном',
        related_name='favorited'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь избранного',
        related_name='favorites'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_favorite_recipe-user',
                violation_error_message='Рецепт уже в избранном.'
            )
        ]

    def __str__(self):
        return self.recipe.name


class ShoppingList(models.Model):
    """Класс модели для Списка покупок."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт в списке покупок',
        related_name='shopping_listed'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь списка покупок',
        related_name='shopping_lists',
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списках покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_shopping_list_recipe-user',
                violation_error_message='Рецепт уже в списке покупок.'
            )
        ]

    def __str__(self):
        return self.recipe.name
