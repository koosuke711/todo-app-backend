# Generated by Django 5.1 on 2024-09-07 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0005_task_end_time_task_start_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='start_time',
            field=models.DateTimeField(),
        ),
    ]
