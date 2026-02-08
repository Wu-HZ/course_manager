# Generated migration for removing combined class group models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_teacherqualification_priority'),
    ]

    operations = [
        # First remove the foreign key field from Teacher
        migrations.RemoveField(
            model_name='teacher',
            name='combined_class_group',
        ),
        # Then remove the models (order matters due to FK from CombinedClassSet to CombinedClassGroup)
        migrations.DeleteModel(
            name='CombinedClassSet',
        ),
        migrations.DeleteModel(
            name='CombinedClassGroup',
        ),
    ]
