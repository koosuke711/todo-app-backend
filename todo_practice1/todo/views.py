from rest_framework import viewsets, generics, permissions, status
from rest_framework.views import APIView
from .models import Project, Tab, Task
from django.contrib.auth.models import User
from .serializers import ProjectSerializer, TabSerializer, TaskSerializer, UserSerializer
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.password_validation import validate_password

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        # プロジェクトが削除されると関連するタグとタスクも削除
        instance.tabs.all().delete()
        instance.delete()

    # プロジェクトツリーを保存するエンドポイント
    @action(detail=True, methods=['post'])
    def save_tree(self, request, pk=None):
        project = self.get_object()
        project.tree_data = request.data  # nodes と edges を含むJSONデータを保存
        project.save()
        return Response({'status': 'ツリーが保存されました'}, status=status.HTTP_200_OK)
    
class TabViewSet(viewsets.ModelViewSet):
    queryset = Tab.objects.all()
    serializer_class = TabSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project = self.request.query_params.get('project', None)
        if project:
            return Tab.objects.filter(project__id=project)
        return super().get_queryset()
    
    def perform_create(self, serializer):
        project_id = self.request.data.get('project')
        project = Project.objects.get(id=project_id)  # プロジェクトを取得
        serializer.save(project=project)  # プロジェクトを設定して保存

    def perform_update(self, serializer):
        project_id = self.request.data.get('project')
        project = Project.objects.get(id=project_id)  # プロジェクトを取得
        serializer.save(project=project)  # プロジェクトを設定して保存

    def perform_destroy(self, instance):
        # タグが削除されると関連するタスクも削除
        instance.tasks.all().delete()
        instance.delete()

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 現在ログインしているユーザーのタスクのみを返す
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # POSTデータからproject_idとtab_idを取得し、適切に外部キーを設定する
        project_id = self.request.data.get('project')
        tab_id = self.request.data.get('tab')

        # プロジェクトとタブを取得して関連付ける
        project = Project.objects.get(id=project_id)
        tab = Tab.objects.get(id=tab_id)

        # タスクを保存し、user, project, tabを設定
        serializer.save(user=self.request.user, project=project, tab=tab)

    def perform_update(self, serializer):
        # タスク更新時にproject_idとtab_idがPOSTされるので、それに基づいて更新する
        project_id = self.request.data.get('project')
        tab_id = self.request.data.get('tab')

        # プロジェクトとタブを取得して関連付ける
        project = Project.objects.get(id=project_id)
        tab = Tab.objects.get(id=tab_id)

        # タスクを保存し、user, project, tabを設定
        serializer.save(user=self.request.user, project=project, tab=tab)


# 通知用のタスク取得ビュー
class TaskNotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        now = timezone.now()
        one_minute_from_now = now + timezone.timedelta(minutes=1)

        # 現在のユーザーのタスクで、1分以内に開始されるタスクを取得
        tasks = Task.objects.filter(
            user=request.user,
            scheduled_start_time__gte=now,  # 現在時刻以降に開始
            scheduled_start_time__lte=one_minute_from_now  # 1分以内に開始
        )

        return Response({
            "tasks": list(tasks.values("id", "title", "scheduled_start_time"))
        })

# ユーザー管理用のビュー
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return super(UserViewSet, self).get_permissions()
    
    # 認証されたユーザーの詳細情報を取得するカスタムアクション
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='me')
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    # パスワード変更用のアクション
    @action(detail=False, methods=['patch'], permission_classes=[permissions.IsAuthenticated], url_path='change-password')
    def change_password(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        # 現在のパスワードが正しいか確認
        if not user.check_password(old_password):
            print('現在のパスワードが正しくありません。')
            return Response({'old_password': ['現在のパスワードが正しくありません。']}, status=status.HTTP_400_BAD_REQUEST)

        # 新しいパスワードを検証
        try:
            validate_password(new_password, user=user)
        except Exception as e:
            print(e)
            return Response({'new_password': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        # パスワードを変更
        user.set_password(new_password)
        user.save()

        return Response({'detail': 'パスワードが正常に変更されました。'}, status=status.HTTP_200_OK)

