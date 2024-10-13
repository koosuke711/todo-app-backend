from rest_framework import viewsets, status
from rest_framework.views import APIView
from .models import Project, Tab, Task
from django.contrib.auth.models import User
from .serializers import ProjectSerializer, TabSerializer, TaskSerializer, UserSerializer
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_encode
from django.utils.encoding import force_bytes

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # tabの外部キーにprojectを設定してあるし、カスケードしてあるからこの処理は不要
    # def perform_destroy(self, instance):
    #     # プロジェクトが削除されると関連するタグとタスクも削除
    #     instance.tabs.all().delete()
    #     instance.delete()

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
    permission_classes = [IsAuthenticated]

    # 特定のプロジェクトのタブだけを返すようにしたい。（リクエストにproject_idを含める必要がある）
    # if文がおそらく冗長（return Project.objects.filter(user=self.request.user)こんな感じでいけるはず）
    def get_queryset(self):
        project = self.request.query_params.get('project', None)
        if project:
            return Tab.objects.filter(project__id=project)
        return super().get_queryset()
    
    # リクエストボディにprojectは入っているし、シリアライザに設定もしてあるからこの処理は不要
    # def perform_create(self, serializer):
    #     project_id = self.request.data.get('project')
    #     project = Project.objects.get(id=project_id)  # プロジェクトを取得
    #     serializer.save(project=project)  # プロジェクトを設定して保存

    # リクエストボディにprojectは入っているし、シリアライザに設定もしてあるからこの処理は不要
    # def perform_update(self, serializer):
    #     project_id = self.request.data.get('project')
    #     project = Project.objects.get(id=project_id)  # プロジェクトを取得
    #     serializer.save(project=project)  # プロジェクトを設定して保存

    # taskの外部キーにtabを設定してあるし、カスケードしてあるからこの処理は不要
    # def perform_destroy(self, instance):
    #     # タグが削除されると関連するタスクも削除
    #     instance.tasks.all().delete()
    #     instance.delete()

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

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

# この機能もおそらく不要（フロントエンドで時間を管理している）
# 通知用のタスク取得ビュー
class TaskNotificationView(APIView):
    permission_classes = [IsAuthenticated]

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

    # ユーザー作成の時だけは認証は不要に設定
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]

        return super(UserViewSet, self).get_permissions()
    
    # # これもフィルターをかければカスタムしなくともいけるはず
    # # 認証されたユーザーの詳細情報を取得するカスタムアクション
    # @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='me')
    # def me(self, request):
    #     user = request.user
    #     serializer = self.get_serializer(user)
    #     return Response(serializer.data)
    
    def get_queryset(self):
        # 現在ログインしているユーザーの情報のみを返す
        return User.objects.filter(username=self.request.user)
    
    # パスワード変更用のアクション
    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated], url_path='change-password')
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
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='password-reset')
    def password_reset(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'email': 'メールアドレスは必須です。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'email': 'このメールアドレスは登録されていません。'}, status=status.HTTP_400_BAD_REQUEST)

        # パスワードリセット用のトークン生成
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # リセットリンクの作成（フロントエンドのパスワードリセットページのURLを設定）
        reset_url = f"http://localhost:3000/password-reset-confirm?uid={uid}&token={token}"

        # メール送信
        send_mail(
            subject='パスワードリセットのリクエスト',
            message=f'以下のリンクからパスワードの再設定を行ってください: {reset_url}',
            from_email='no-reply@example.com',
            recipient_list=[email],
        )

        return Response({'detail': 'パスワードリセット用のリンクをメールアドレスに送信しました。'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='reset-password-confirm')
    def reset_password_confirm(self, request):
        uidb64 = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not uidb64 or not token or not new_password:
            return Response({'detail': '全てのフィールドが必須です。'}, status=status.HTTP_400_BAD_REQUEST)

        # UIDをデコードしてユーザーを取得
        try:
            uid = urlsafe_base64_encode(uidb64).decode()  # ここでエラーが出るかもしれない
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': '無効なリンクです。'}, status=status.HTTP_400_BAD_REQUEST)

        # トークンを検証
        if not default_token_generator.check_token(user, token):
            return Response({'detail': '無効なリンクです。'}, status=status.HTTP_400_BAD_REQUEST)

        # パスワードをリセット
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'パスワードが正常にリセットされました。'}, status=status.HTTP_200_OK)

