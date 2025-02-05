import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import (
    UserCreateSerializer,
    UserSerializer,
    ValidationError
)
from rest_framework import serializers

from core.constants import MAX_LENGTH_USER_NAME
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingList,
    Tag
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    first_name = serializers.CharField(
        required=True,
        max_length=MAX_LENGTH_USER_NAME
    )
    last_name = serializers.CharField(
        required=True,
        max_length=MAX_LENGTH_USER_NAME
    )


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField(default=None)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.subscriptions.filter(subscription=obj).exists()
        )

    def get_avatar(self, obj):
        return obj.avatar.url if obj.avatar else None


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
            'recipes',
            'recipes_count'
        )
        read_only_fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
            'recipes',
            'recipes_count'
        )

    def validate(self, data):
        request = self.context.get('request')
        subscription = self.instance
        user = request.user
        method = request.method
        subscription_availability = subscription.subscribers.filter(
            subscriber=user
        ).exists()

        if method == 'POST':
            if user == subscription:
                raise ValidationError(
                    'Попытка подписки на себя.'
                )
            if subscription_availability:
                raise ValidationError(
                    'Подписка уже оформлена.'
                )
        if method == 'DELETE' and not subscription_availability:
            raise ValidationError(
                'Нет такой подписки.'
            )
        return data

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.author_recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeShortSerializer(recipes, many=True).data


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


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


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Класс сериализатора для ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Класс сериализатора для рецептов."""

    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='ingredients_in_recipe'
    )
    tags = TagSerializer(many=True, read_only=True)

    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=False, allow_null=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'image', 'name',
                  'text', 'cooking_time', 'is_favorited',
                  'is_in_shopping_cart')
        read_only_fields = ('is_favorited', 'is_in_shopping_cart')

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Не передан ни один ингредиент.'
            )
        if len(ingredients) > len({item['id'] for item in ingredients}):
            raise serializers.ValidationError('Дублирующиеся ингридиенты')

        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Не передан ни один тэг.'
            )
        if len(tags) > len(set(tags)):
            raise serializers.ValidationError('Дублирующиеся тэги')

        for tag_id in tags:
            try:
                Tag.objects.get(id=tag_id)
            except Tag.DoesNotExist:
                raise serializers.ValidationError(f'Нет тега c id = {tag_id}.')

        return data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.favorited.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.shopping_listed.filter(user=request.user).exists()
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients_in_recipe', [])
        tags = self.initial_data.get('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.add_ingredients_in_recipe(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        instance.save()
        ingredients_data = validated_data.pop('ingredients_in_recipe', [])
        tags = self.initial_data.get('tags', [])
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.add_ingredients_in_recipe(instance, ingredients_data)
        return instance

    def add_ingredients_in_recipe(self, recipe, ingredients_for_ricipe):
        for ingredient in ingredients_for_ricipe:
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )


class RecipeShortSerializer(serializers.ModelSerializer):
    """Класс сериализатора для рецептов без тегов и ингредиентов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
