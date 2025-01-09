from rest_framework import serializers

from recipes.models import Favorite, Ingredient, Recipe, ShoppingList, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', 'name', 'measurement_unit')


class FavoriteShoppingListBaseSerializer(serializers.ModelSerializer):
    """Базовый класс для сериализаторов Избранного и Списка покупок."""

    id = serializers.IntegerField(source='recipe.id')
    name = serializers.CharField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', required=False)
    cooking_time = serializers.IntegerField(source='recipe.cooking_time')

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(FavoriteShoppingListBaseSerializer):
    """Класс сериализатора для Избранного."""

    class Meta(FavoriteShoppingListBaseSerializer.Meta):
        model = Favorite


class ShoppingListSerializer(FavoriteShoppingListBaseSerializer):
    """Класс сериализатора для Списка покупок."""

    class Meta(FavoriteShoppingListBaseSerializer.Meta):
        model = ShoppingList
