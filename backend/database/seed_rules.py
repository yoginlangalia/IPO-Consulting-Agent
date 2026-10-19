"""Script to seed SEBI ICDR rules into the database permanently."""
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import SessionLocal, init_db
from database.models import SebiRule


def seed_rules():
    """Load rules from JSON and insert into database if not already present."""
    rules_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "rules",
        "sebi_icdr_rules.json"
    )

    with open(rules_path, "r", encoding="utf-8") as f:
        rules_data = json.load(f)

    db = SessionLocal()
    try:
        inserted = 0
        skipped = 0
        for rule in rules_data:
            existing = db.query(SebiRule).filter(
                SebiRule.rule_code == rule["rule_code"]
            ).first()

            if existing:
                skipped += 1
                continue

            db_rule = SebiRule(
                rule_code=rule["rule_code"],
                regulation=rule["regulation"],
                category=rule["category"],
                title=rule["title"],
                description=rule["description"],
                threshold_value=rule.get("threshold_value"),
                check_type=rule["check_type"],
                data_source=rule.get("data_source"),
                route=rule.get("route"),
            )
            db.add(db_rule)
            inserted += 1

        db.commit()
        print(f"Seeding complete: {inserted} rules inserted, {skipped} already existed.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding rules: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    seed_rules()
