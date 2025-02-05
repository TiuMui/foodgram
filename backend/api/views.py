from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingListSerializer,
    SubscriptionSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingList,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Класс для представления пользователя."""

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        return super().me(request)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        subscriber = request.user
        author = get_object_or_404(
            User.objects.annotate(
                recipes_count=Count('author_recipes')
            ),
            id=id
        )

        serializer = SubscriptionSerializer(
            author,
            data={},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        if request.method == 'POST':
            Subscription.objects.create(
                subscriber=subscriber,
                subscription=author
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        Subscription.objects.filter(
            subscriber=subscriber,
            subscription=author
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscriber = request.user
        queryset = User.objects.filter(
            subscribers__subscriber=subscriber
        ).annotate(
            recipes_count=Count('author_recipes')
        )
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class AvatarAPIView(APIView):
    """Класс для представления аватара."""

    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = AvatarSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'avatar': serializer.data['avatar']})

    def delete(self, request):
        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Класс для представления тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """класс для представления ингредиентов."""

    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        search_value = self.request.query_params.get('name', None)
        if search_value:
            queryset = queryset.filter(name__istartswith=search_value.lower())
        return queryset


class FavoriteShoppingListBaseAPIView(APIView):
    """Базовый класс для представлений Избранного и Списка покупок."""

    def add_recipe(self, request, recipe_id, model, serializer_class):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        favorite = model(user=user, recipe=recipe)
        favorite.save()
        serializer = serializer_class(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_recipe(self, request, recipe_id, model):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        favorite = model.objects.filter(user=user, recipe=recipe).first()
        if not favorite:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteAPIView(FavoriteShoppingListBaseAPIView):
    """Класс для представления Избранного."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, recipe_id):
        return self.add_recipe(
            request,
            recipe_id,
            Favorite,
            FavoriteSerializer
        )

    def delete(self, request, recipe_id):
        return self.remove_recipe(request, recipe_id, Favorite)


class ShoppingListAPIView(FavoriteShoppingListBaseAPIView):
    """Класс для представления Списка покупок."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, recipe_id):
        return self.add_recipe(
            request,
            recipe_id,
            ShoppingList,
            ShoppingListSerializer
        )

    def delete(self, request, recipe_id):
        return self.remove_recipe(request, recipe_id, ShoppingList)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Recipe.objects.prefetch_related('tags').all()
        user = self.request.user
        user_auth = user.is_authenticated
        query_params = self.request.query_params

        tags = query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        author = query_params.get('author')
        if author:
            queryset = queryset.filter(author=author)

        is_favorited = query_params.get('is_favorited')
        if is_favorited == '1' and user_auth:
            queryset = queryset.filter(favorited__user=user)

        is_in_shopping_cart = query_params.get('is_in_shopping_cart')
        if is_in_shopping_cart == '1' and user_auth:
            queryset = queryset.filter(shopping_listed__user=user)

        return queryset

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        user = request.user
        items = (
            IngredientInRecipe.objects.filter(
                recipe__shopping_listed__user=user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit'
            ).annotate(
                amount=Sum('amount')
            ).order_by('ingredient__name')
        )

        shopping_list = ''
        for item in items:
            shopping_list += (
                f"{item['ingredient__name']}, "
                f"{item['ingredient__measurement_unit']} "
                f"- {item['amount']}\n"
            )
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="Список покупок.txt"')
        return response

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        part_of_url = recipe.short_hash
        url = request.build_absolute_uri(f'/s/{part_of_url}/')
        return Response({'short-link': url}, status=status.HTTP_200_OK)
