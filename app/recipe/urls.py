from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views


router = DefaultRouter()
router.register('tags', views.TagViewSet)
router.register('ingredients', views.IngredientViewSet)

# used in reverse function to identify url path
app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]
