from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_teacher_min_max_hours'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='is_main_subject',
            field=models.BooleanField(
                default=False,
                help_text='主课(如语文数学英语)，同一教师只能教一门主课',
                verbose_name='主课'
            ),
        ),
    ]
