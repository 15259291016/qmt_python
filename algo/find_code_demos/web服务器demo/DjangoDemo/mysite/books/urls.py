from .views import index
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SnippetList, SnippetDetail
router = DefaultRouter()
# 如果使用视图集可以注册视图集
# router.register(r'snippets', views.SnippetViewSet)
urlpatterns = [
    path('', index, name='index'),
    path('', include(router.urls)),
    path('snippets/', SnippetList.as_view(), name='snippet-list'),
    path('snippets/<int:pk>/', SnippetDetail.as_view(), name='snippet-detail'),
]