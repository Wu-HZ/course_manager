# Generated migration for restoring CombinedClassGroup and making ScheduleEntry.teacher nullable
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_remove_combined_class_models'),
        ('scheduler', '0001_initial'),
    ]

    operations = [
        # 1. Recreate CombinedClassGroup model
        migrations.CreateModel(
            name='CombinedClassGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='分组名称')),
            ],
            options={
                'verbose_name': '校本课程分组',
                'verbose_name_plural': '校本课程分组',
            },
        ),
        # 2. Recreate Teacher.combined_class_group FK
        migrations.AddField(
            model_name='teacher',
            name='combined_class_group',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='core.combinedclassgroup',
                verbose_name='校本课程分组'
            ),
        ),
    ]
