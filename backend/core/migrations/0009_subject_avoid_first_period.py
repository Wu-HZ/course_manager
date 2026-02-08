from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_subject_applicable_grades'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='avoid_first_period',
            field=models.BooleanField(
                default=False, help_text='勾选后尽量不安排在每天第一节课',
                verbose_name='避免第一节'
            ),
        ),
    ]
