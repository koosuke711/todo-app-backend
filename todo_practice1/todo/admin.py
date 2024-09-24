from django.contrib import admin
from .models import Project, Tab, Task

# Projectモデルのidフィールドを表示
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')  # idとnameを表示

# Tabモデルのidフィールドを表示
class TabAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'project')  # id、name、projectを表示

# Taskモデルのidフィールドを表示
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'project', 'tab')  # id、title、project、tabを表示

# 管理画面に登録
admin.site.register(Project, ProjectAdmin)
admin.site.register(Tab, TabAdmin)
admin.site.register(Task, TaskAdmin)
