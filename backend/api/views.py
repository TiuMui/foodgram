from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             ShoppingListSerializer, TagSerializer)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingList, Tag


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


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
