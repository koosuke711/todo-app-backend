from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    tree_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name
    
class Tab(models.Model):
    project = models.ForeignKey(Project, related_name='tabs', on_delete=models.CASCADE)  # プロジェクトに関連付けられたタグ
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Task(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # 送られてくる情報
    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE)  # プロジェクトと紐付け
    tab = models.ForeignKey(Tab, related_name='tasks', on_delete=models.CASCADE, null=True, blank=True, default=None)  # タブと紐付け

    # タスクフィールド
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=10, default='未着手')
    
    background = models.TextField(null=True, blank=True)  # 背景
    purpose = models.TextField(null=True, blank=True)  # 目的
    description = models.TextField(null=True, blank=True)  # 詳細説明

    # 日付と時間
    scheduled_start_time = models.DateTimeField(null=True, blank=True)  # 開始予定日時
    due_date = models.DateTimeField(null=True, blank=True)  # 締め切り
    actual_start_time = models.DateTimeField(null=True, blank=True)  # 実際の開始日時
    completion_date = models.DateTimeField(null=True, blank=True)  # 完了時
    
    overtime = models.IntegerField(null=True, blank=True)  # 超過時間（分単位）
    difficulty = models.IntegerField(null=True, blank=True)  # 難易度（1-10段階）
    expected_work_time = models.IntegerField(null=True, blank=True)  # 想定作業時間（分単位）
    actual_work_time = models.IntegerField(null=True, blank=True)  # 想定作業時間（分単位）

    # 達成度とコメント
    achievement = models.FloatField(null=True, blank=True)  # 達成度（%）
    comment = models.TextField(null=True, blank=True)  # コメント

    def __str__(self):
        return self.title

    
