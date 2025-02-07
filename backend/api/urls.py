from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    AvatarAPIView,
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
)

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
