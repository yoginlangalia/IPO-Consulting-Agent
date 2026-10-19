import sqlite3
import os

for path in ['ipo_agent.db', 'backend/ipo_agent.db']:
    if os.path.exists(path):
        print(f"Migrating {path}...")
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute('PRAGMA table_info(companies)')
        cols = [row[1] for row in cursor.fetchall()]
        print('Existing columns:', cols)

        new_cols = [
            ('sector', 'VARCHAR(255)'),
            ('incorporation_year', 'INTEGER'),
            ('target_track', 'VARCHAR(50) DEFAULT "REG_6_1"'),
            ('target_ipo_date', 'VARCHAR(100)'),
            ('description', 'TEXT'),
            ('financial_data', 'JSON'),
            ('readiness_score', 'FLOAT'),
            ('eligibility_status', 'VARCHAR(50) DEFAULT "PENDING"'),
        ]

        for col_name, col_type in new_cols:
            if col_name not in cols:
                print(f'Adding column {col_name}...')
                cursor.execute(f'ALTER TABLE companies ADD COLUMN {col_name} {col_type}')

        conn.commit()
        conn.close()
        print(f'{path} migration complete!')
