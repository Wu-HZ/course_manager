from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_subject_avoid_first_period'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduleLock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField(choices=[(0, '周一'), (1, '周二'), (2, '周三'), (3, '周四'), (4, '周五')], verbose_name='星期')),
                ('period', models.IntegerField(verbose_name='节次')),
                ('school_class', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_locks', to='core.schoolclass', verbose_name='班级')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.subject', verbose_name='课程')),
                ('teacher', models.ForeignKey(blank=True, help_text='留空则使用授课分配中的教师', null=True, on_delete=django.db.models.deletion.CASCADE, to='core.teacher', verbose_name='教师')),
            ],
            options={
                'verbose_name': '课表锁定',
                'verbose_name_plural': '课表锁定',
                'unique_together': {('school_class', 'day', 'period')},
            },
        ),
    ]
