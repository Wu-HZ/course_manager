from django.db import migrations


LEGACY_SCHEDULER_SETTINGS_COLUMNS = {
    'f2_enable_homeroom_main_subject',
    'f3_enable_single_main_subject_teacher',
    'f4_enable_subject_teacher_class_limit',
    'h4_enable_day_off',
    'h5_enable_location_capacity',
    'h8_enable_max_daily_limit',
    'h9_enable_consecutive_forbidden',
    'h10_enable_teacher_weekly_limits',
    'h11_enable_teacher_class_daily_limit',
    'h12_enable_combined_teacher_constraint',
    'h13_enable_teacher_blocked_times',
}

CURRENT_SCHEDULER_SETTINGS_COLUMNS = [
    ('id', 'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT'),
    ('h9_consecutive_forbidden', 'varchar(50) NOT NULL'),
    ('h11_teacher_class_daily_max', 'INTEGER NOT NULL'),
    ('s1_am_preference_weight', 'INTEGER NOT NULL'),
    ('s2_consecutive_weight', 'INTEGER NOT NULL'),
    ('s3_distribution_weight', 'INTEGER NOT NULL'),
    ('s4_teacher_daily_threshold', 'INTEGER NOT NULL'),
    ('s4_teacher_daily_weight', 'INTEGER NOT NULL'),
    ('s6_subject_switch_weight', 'INTEGER NOT NULL'),
    ('s7_same_class_subject_switch_weight', 'INTEGER NOT NULL'),
    ('class_meeting_name', 'varchar(50) NOT NULL'),
    ('combined_class_slots', 'varchar(100) NOT NULL'),
    ('solver_num_workers', 'INTEGER NOT NULL'),
    ('s5_avoid_first_weight', 'INTEGER NOT NULL'),
]


def normalize_scheduler_settings_schema(apps, schema_editor):
    if schema_editor.connection.vendor != 'sqlite':
        return

    table_name = 'core_schedulersettings'
    normalized_table_name = f'{table_name}_normalized'
    current_column_names = [name for name, _ in CURRENT_SCHEDULER_SETTINGS_COLUMNS]

    with schema_editor.connection.cursor() as cursor:
        table_info = cursor.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        if not table_info:
            return

        existing_column_names = [row[1] for row in table_info]
        if not LEGACY_SCHEDULER_SETTINGS_COLUMNS.intersection(existing_column_names):
            return

        missing_columns = [
            column_name
            for column_name in current_column_names
            if column_name not in existing_column_names
        ]
        if missing_columns:
            missing_display = ', '.join(missing_columns)
            raise RuntimeError(
                f'core_schedulersettings 缺少当前字段，无法自动规范化: {missing_display}'
            )

        cursor.execute(f'DROP TABLE IF EXISTS "{normalized_table_name}"')

        column_definitions = ', '.join(
            f'"{column_name}" {column_sql}'
            for column_name, column_sql in CURRENT_SCHEDULER_SETTINGS_COLUMNS
        )
        cursor.execute(
            f'CREATE TABLE "{normalized_table_name}" ({column_definitions})'
        )

        column_list = ', '.join(
            f'"{column_name}"'
            for column_name in current_column_names
        )
        cursor.execute(
            f'INSERT INTO "{normalized_table_name}" ({column_list}) '
            f'SELECT {column_list} FROM "{table_name}"'
        )
        cursor.execute(f'DROP TABLE "{table_name}"')
        cursor.execute(
            f'ALTER TABLE "{normalized_table_name}" RENAME TO "{table_name}"'
        )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('core', '0023_add_import_keys'),
    ]

    operations = [
        migrations.RunPython(
            normalize_scheduler_settings_schema,
            migrations.RunPython.noop,
        ),
    ]
