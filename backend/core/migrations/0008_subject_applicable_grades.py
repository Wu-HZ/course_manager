from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_teacher_must_reach_max_hours'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='applicable_grades',
            field=models.CharField(
                blank=True, default='', help_text='逗号分隔的年级列表，如"1,2,3"。留空表示所有年级',
                max_length=50, verbose_name='适用年级'
            ),
        ),
    ]
