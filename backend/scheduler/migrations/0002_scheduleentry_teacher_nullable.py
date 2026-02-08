# Make ScheduleEntry.teacher nullable for combined class entries
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0001_initial'),
        ('core', '0005_restore_combined_class_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheduleentry',
            name='teacher',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.teacher',
                verbose_name='教师'
            ),
        ),
    ]
