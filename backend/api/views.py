from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import CustomSearchFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingListSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserRecipeSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingList,
    Tag,
)

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
        methods=['post'],
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
            data={'subscriber': subscriber.id, 'subscription': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        subscriber = request.user
        author = get_object_or_404(User, id=id)
        deleted, _ = subscriber.subscriptions.filter(
            subscription=author
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Нет такой подписки.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': 'Успешная отписка'}, status=status.HTTP_204_NO_CONTENT
        )

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
        serializer = UserRecipeSerializer(
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

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (CustomSearchFilter, )
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.prefetch_related('tags').all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

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
                f"{item['ingredient__name']} "
                f"- {item['amount']} "
                f"{item['ingredient__measurement_unit']}\n"
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

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        return self.add_del_favorite_shopping_cart(
            request,
            pk,
            Favorite,
            FavoriteSerializer
        )

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        return self.add_del_favorite_shopping_cart(
            request,
            pk,
            ShoppingList,
            ShoppingListSerializer
        )

    def add_del_favorite_shopping_cart(
            self,
            request,
            pk,
            model,
            serializer_class
    ):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            obj = model(user=user, recipe=recipe)
            obj.save()
            serializer = serializer_class(obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        obj = model.objects.filter(user=user, recipe=recipe).first()
        if not obj:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
