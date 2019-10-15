from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views


router = DefaultRouter()
router.register('tags', views.TagViewSet)

# used in reverse function to identify url path
app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]
