from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from todo.views import ProjectViewSet, TabViewSet, TaskViewSet, UserViewSet, TaskNotificationView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'tabs', TabViewSet)
router.register(r'users', UserViewSet, basename='user')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/task-notifications/', TaskNotificationView.as_view(), name='task-notifications'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # JWTトークン取得用エンドポイント
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # JWTトークンリフレッシュ用エンドポイント
]
