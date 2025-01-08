from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, TagViewSet


router_constructor = (
    ('tags', TagViewSet, 'tags'),
    ('ingredients', IngredientViewSet, 'ingredients'),
)
router = DefaultRouter()

for url_prefix, view_set, base_name in router_constructor:
    router.register(url_prefix, view_set, basename=base_name)

urlpatterns = [
    path('', include(router.urls)),
]
