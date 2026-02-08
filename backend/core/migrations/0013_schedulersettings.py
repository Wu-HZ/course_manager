from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_subject_is_main_subject'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchedulerSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('h9_consecutive_forbidden', models.CharField(
                    default='1,2', help_text='禁止连堂跨越的节次对，格式如"1,2"表示第2-3节之间',
                    max_length=50, verbose_name='连堂禁跨节次对'
                )),
                ('h11_teacher_class_daily_max', models.IntegerField(
                    default=2, help_text='同一教师同一天在同一班级最多上几节课',
                    verbose_name='教师同班单日上限'
                )),
                ('s1_am_preference_weight', models.IntegerField(
                    default=10, help_text='标记"上午优先"的课程排在上午的奖励分',
                    verbose_name='上午优先权重'
                )),
                ('s2_consecutive_weight', models.IntegerField(
                    default=5, help_text='允许连堂的课程连续排列的奖励分',
                    verbose_name='连堂偏好权重'
                )),
                ('s3_distribution_weight', models.IntegerField(
                    default=2, help_text='同课同班同天超过1节的惩罚分',
                    verbose_name='分布均匀权重'
                )),
                ('s4_teacher_daily_threshold', models.IntegerField(
                    default=3, help_text='教师单日课时超过此值开始惩罚',
                    verbose_name='教师日负载阈值'
                )),
                ('s4_teacher_daily_weight', models.IntegerField(
                    default=8, help_text='教师单日课时超出阈值的惩罚分',
                    verbose_name='教师日负载权重'
                )),
                ('s5_avoid_first_weight', models.IntegerField(
                    default=6, help_text='标记"避免第一节"的课程排在第一节的惩罚分',
                    verbose_name='避免第一节权重'
                )),
                ('s6_subject_switch_weight', models.IntegerField(
                    default=5, help_text='教师连续两节不同科目的惩罚分',
                    verbose_name='换科惩罚权重'
                )),
            ],
            options={
                'verbose_name': '排课参数设置',
                'verbose_name_plural': '排课参数设置',
            },
        ),
    ]
