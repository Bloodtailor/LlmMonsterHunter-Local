# Dev Database Column Add - abilities schema v2 (Numeric Core NC-M1)
# db.create_all() never ALTERs existing tables and this project has no
# migration tooling, so this one-off script adds the six v2 tier-word
# columns to the DEV database without touching any data (reset_db.py
# remains the nuclear option). Idempotent - safe to run any number of
# times.
#
# What it does: ALTER TABLE abilities ADD COLUMN for element, power,
# cost_pool, cost, target, effect (each skipped if it already exists).
# NO backfill: legacy prose-only abilities stay NULL by design - prompt
# renderers fall back to prose lines, and New Game is the migration.
#
# Usage: python -m backend.tests.add_ability_v2_columns   (from project root)

import os

from flask import Flask

V2_COLUMNS = (
    ('element', 'VARCHAR(20) NULL'),
    ('power', 'VARCHAR(20) NULL'),
    ('cost_pool', 'VARCHAR(10) NULL'),
    ('cost', 'VARCHAR(20) NULL'),
    ('target', 'VARCHAR(20) NULL'),
    ('effect', 'VARCHAR(20) NULL'),
)


def build_minimal_app():
    """A Flask app with ONLY the database configured - no LLM load,
    no AI queue, no ComfyUI check (reset_db.py pattern)"""

    from backend.models.core import init_db

    app = Flask(__name__)

    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME', 'monster_hunter_game')

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    init_db(app)
    return app


def column_exists(db, table: str, column: str) -> bool:
    from sqlalchemy import inspect

    return any(col['name'] == column for col in inspect(db.engine).get_columns(table))


def main():
    db_name = os.getenv('DB_NAME', 'monster_hunter_game')
    print('🧮 ABILITY SCHEMA V2 COLUMN ADD')
    print('=' * 50)
    print(f"Database: '{db_name}' - adds six abilities columns, touches nothing else.")

    app = build_minimal_app()
    from backend.models.core import db

    with app.app_context():
        from sqlalchemy import text

        for column, definition in V2_COLUMNS:
            if column_exists(db, 'abilities', column):
                print(f'Column abilities.{column} already exists - skipped.')
                continue
            db.session.execute(text(f'ALTER TABLE abilities ADD COLUMN {column} {definition}'))
            db.session.commit()
            print(f'Added column abilities.{column} ({definition}).')

        print('🎉 Done.')


if __name__ == '__main__':
    main()
