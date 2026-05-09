import uuid

import core.models
from django.core.validators import RegexValidator
from django.db import migrations, models


MODELS_WITH_IMPORT_KEY = (
    'travelgroup',
    'subject',
    'combinedclassgroup',
    'teacher',
    'schoolclass',
    'location',
)


def populate_import_keys(apps, schema_editor):
    for model_name in MODELS_WITH_IMPORT_KEY:
        model = apps.get_model('core', model_name)
        for obj in model.objects.filter(import_key__isnull=True):
            obj.import_key = uuid.uuid4().hex
            obj.save(update_fields=['import_key'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_teacherblockedtime'),
    ]

    operations = [
        migrations.AddField(
            model_name='combinedclassgroup',
            name='import_key',
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=32, null=True, unique=True, verbose_name='导入键'),
        ),
        migrations.AddField(
            model_name='location',
            name='import_key',
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=32, null=True, unique=True, verbose_name='导入键'),
        ),
        migrations.AddField(
            model_name='schoolclass',
            name='import_key',
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=32, null=True, unique=True, verbose_name='导入键'),
        ),
        migrations.AddField(
            model_name='subject',
            name='import_key',
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=32, null=True, unique=True, verbose_name='导入键'),
        ),
        migrations.AddField(
            model_name='teacher',
            name='import_key',
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=32, null=True, unique=True, verbose_name='导入键'),
        ),
        migrations.AddField(
            model_name='travelgroup',
            name='import_key',
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=32, null=True, unique=True, verbose_name='导入键'),
        ),
        migrations.RunPython(populate_import_keys, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='combinedclassgroup',
            name='import_key',
            field=models.CharField(db_index=True, default=core.models.generate_import_key, editable=False, help_text='系统生成的稳定导入键，用于导入导出时精确关联。', max_length=32, unique=True, validators=[RegexValidator(message='导入键格式无效。', regex='^[0-9a-f]{32}$')], verbose_name='导入键'),
        ),
        migrations.AlterField(
            model_name='location',
            name='import_key',
            field=models.CharField(db_index=True, default=core.models.generate_import_key, editable=False, help_text='系统生成的稳定导入键，用于导入导出时精确关联。', max_length=32, unique=True, validators=[RegexValidator(message='导入键格式无效。', regex='^[0-9a-f]{32}$')], verbose_name='导入键'),
        ),
        migrations.AlterField(
            model_name='schoolclass',
            name='import_key',
            field=models.CharField(db_index=True, default=core.models.generate_import_key, editable=False, help_text='系统生成的稳定导入键，用于导入导出时精确关联。', max_length=32, unique=True, validators=[RegexValidator(message='导入键格式无效。', regex='^[0-9a-f]{32}$')], verbose_name='导入键'),
        ),
        migrations.AlterField(
            model_name='subject',
            name='import_key',
            field=models.CharField(db_index=True, default=core.models.generate_import_key, editable=False, help_text='系统生成的稳定导入键，用于导入导出时精确关联。', max_length=32, unique=True, validators=[RegexValidator(message='导入键格式无效。', regex='^[0-9a-f]{32}$')], verbose_name='导入键'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='import_key',
            field=models.CharField(db_index=True, default=core.models.generate_import_key, editable=False, help_text='系统生成的稳定导入键，用于导入导出时精确关联。', max_length=32, unique=True, validators=[RegexValidator(message='导入键格式无效。', regex='^[0-9a-f]{32}$')], verbose_name='导入键'),
        ),
        migrations.AlterField(
            model_name='travelgroup',
            name='import_key',
            field=models.CharField(db_index=True, default=core.models.generate_import_key, editable=False, help_text='系统生成的稳定导入键，用于导入导出时精确关联。', max_length=32, unique=True, validators=[RegexValidator(message='导入键格式无效。', regex='^[0-9a-f]{32}$')], verbose_name='导入键'),
        ),
    ]
