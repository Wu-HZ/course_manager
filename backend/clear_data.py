import argparse
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description='备份并清空当前活动数据库，保留表结构。'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='跳过确认提示，直接执行清空。',
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='跳过自动备份，直接清空当前数据库。',
    )
    return parser.parse_args()


def setup_django():
    backend_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(backend_dir))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    import django

    django.setup()
    return backend_dir


def get_active_sqlite_db_path():
    from django.conf import settings

    database = settings.DATABASES['default']
    engine = database.get('ENGINE')
    if engine != 'django.db.backends.sqlite3':
        raise RuntimeError(f'当前仅支持 SQLite，实际数据库引擎为: {engine}')

    db_name = database.get('NAME')
    if not db_name:
        raise RuntimeError('未找到当前活动数据库路径。')

    return Path(db_name).expanduser().resolve()


def backup_sqlite_database(source_path, backup_dir):
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_path = backup_dir / f'{source_path.stem}-backup-{timestamp}{source_path.suffix}'

    with sqlite3.connect(source_path) as source_conn:
        with sqlite3.connect(backup_path) as backup_conn:
            source_conn.backup(backup_conn)

    return backup_path


def confirm_clear(db_path, backup_enabled):
    print(f'当前活动数据库: {db_path}')
    print('此操作会清空该数据库中的全部数据，包括排课结果，但会保留表结构。')
    if backup_enabled:
        print('脚本会先自动创建备份。')
    else:
        print('已禁用自动备份。')

    confirmation = input('输入 CLEAR 继续，其他任意内容取消: ').strip()
    return confirmation == 'CLEAR'


def clear_database():
    from django.core.management import call_command

    call_command('flush', interactive=False, verbosity=1)


def main():
    args = parse_args()
    backend_dir = setup_django()
    db_path = get_active_sqlite_db_path()

    if not db_path.exists():
        raise FileNotFoundError(f'数据库文件不存在: {db_path}')

    if not args.yes and not confirm_clear(db_path, not args.no_backup):
        print('已取消清空。')
        return 1

    backup_path = None
    if not args.no_backup:
        backup_path = backup_sqlite_database(db_path, backend_dir / 'backups')

    clear_database()

    if backup_path:
        print(f'已备份数据库: {backup_path}')
    print(f'已清空数据库: {db_path}')
    print('表结构已保留，可直接重新导入数据。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
