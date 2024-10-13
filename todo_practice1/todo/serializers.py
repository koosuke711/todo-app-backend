from rest_framework import serializers
from .models import Task, Tab, Project
from django.contrib.auth.models import User

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'tab', 'project', 'title', 'status', 'purpose', 'background', 'description', 'scheduled_start_time', 'due_date', 
                  'actual_start_time', 'completion_date', 'difficulty', 'expected_work_time', 'actual_work_time', 'overtime', 'achievement', 'comment')

class TabSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Tab
        fields = ('id', 'name', 'tasks', 'project')


class ProjectSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name', 'tree_data', 'tasks')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user