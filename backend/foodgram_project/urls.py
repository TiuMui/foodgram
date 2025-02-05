from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect
from django.urls import include, path

from recipes.models import Recipe


def redirect_short_url(request, short_path):
    recipe = get_object_or_404(Recipe, short_hash=short_path)
    url = request.build_absolute_uri(f'/api/recipes/{recipe.id}/')
    return redirect(url)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:short_path>/', redirect_short_url)
]
