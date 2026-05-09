from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_normalize_scheduler_settings_schema'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schedulersettings',
            name='h9_consecutive_forbidden',
            field=models.CharField(
                default='1,2;3,4',
                help_text='禁止教师连续上课跨越的节次对，格式如"1,2;3,4"表示第2-3节和第4-5节之间不能连续上课（0起始）',
                max_length=50,
                verbose_name='教师禁连续上课节次对',
            ),
        ),
    ]
