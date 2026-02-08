from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_schedulelock'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='teacher',
            name='must_reach_max_hours',
        ),
        migrations.AddField(
            model_name='teacher',
            name='min_weekly_hours',
            field=models.IntegerField(
                blank=True, help_text='至少安排多少节课，留空表示不限制',
                null=True, verbose_name='周课时下限'
            ),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='max_weekly_hours',
            field=models.IntegerField(
                blank=True, help_text='至多安排多少节课，留空表示不限制',
                null=True, verbose_name='周课时上限'
            ),
        ),
    ]
