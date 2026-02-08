# Generated manually for combined class refactoring

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_schedulersettings_configurable_params'),
    ]

    operations = [
        # First remove the foreign key field from Teacher
        migrations.RemoveField(
            model_name='teacher',
            name='combined_class_group',
        ),
        # Then delete the CombinedClassGroup model
        migrations.DeleteModel(
            name='CombinedClassGroup',
        ),
    ]
