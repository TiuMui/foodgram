from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (FavoriteAPIView, IngredientViewSet,
                       ShoppingListAPIView, TagViewSet)


router_constructor = (
    ('tags', TagViewSet, 'tags'),
    ('ingredients', IngredientViewSet, 'ingredients'),
)
router = DefaultRouter()

for url_prefix, view_set, base_name in router_constructor:
    router.register(url_prefix, view_set, basename=base_name)

urlpatterns = [
    path('', include(router.urls)),
    path(
        'recipes/<int:recipe_id>/favorite/',
        FavoriteAPIView.as_view(),
        name='favorite-recipe'
    ),
    path(
        'recipes/<int:recipe_id>/shopping_cart/',
        ShoppingListAPIView.as_view(),
        name='shoping_list-recipe'
    ),
]
