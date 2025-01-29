from django.urls import include, path

from rest_framework.routers import DefaultRouter

from api.views import (AvatarAPIView, CustomUserViewSet, FavoriteAPIView,
                       IngredientViewSet, RecipeViewSet, ShoppingListAPIView,
                       TagViewSet)

router_constructor = (
    ('tags', TagViewSet, 'tags'),
    ('ingredients', IngredientViewSet, 'ingredients'),
    ('recipes', RecipeViewSet, 'recipes'),
    ('users', CustomUserViewSet, 'users')
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
    path(
        'users/me/',
        CustomUserViewSet.as_view({'get': 'me'})
    ),
    path(
        'users/set_password/',
        CustomUserViewSet.as_view({'post': 'set_password'}),
        name='set_password'
    ),
    path('users/me/avatar/', AvatarAPIView.as_view(), name='avatar'),
    path('auth/', include('djoser.urls.authtoken'))
]
