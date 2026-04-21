# Generated for schedule result favorite feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0004_scheduleresult_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduleresult',
            name='is_favorite',
            field=models.BooleanField(default=False, verbose_name='收藏'),
        ),
        migrations.AlterModelOptions(
            name='scheduleresult',
            options={
                'ordering': ['-is_favorite', '-created_at'],
                'verbose_name': '排课结果',
                'verbose_name_plural': '排课结果',
            },
        ),
    ]
