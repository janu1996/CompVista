
import sqlite3
from pathlib import Path

db = Path("backend/compvista_backup.db").resolve()

con = sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)
cur = con.cursor()

print("\n===== PROMOTION HISTORY AUDIT =====")
print("Database:", db.name)

# Latest salary record before promotion
# compared with the promotion's previous role and level.
cur.execute("""
    SELECT COUNT(*)
    FROM promotions p
    WHERE EXISTS (
        SELECT 1
        FROM salary_records s
        WHERE s.employee_id = p.employee_id
          AND s.effective_from < p.promotion_date
          AND s.effective_from = (
              SELECT MAX(s2.effective_from)
              FROM salary_records s2
              WHERE s2.employee_id = p.employee_id
                AND s2.effective_from < p.promotion_date
          )
          AND EXISTS (
              SELECT 1
              FROM compensation_bands b
              WHERE b.band_id = s.band_id
                AND (
                    b.role_id != p.previous_role_id
                    OR b.level_id != p.previous_level_id
                )
          )
    )
""")
print("Pre-promotion role/level mismatches:", cur.fetchone()[0])

# Earliest salary record on or after promotion
# compared with the promotion's new role and level.
cur.execute("""
    SELECT COUNT(*)
    FROM promotions p
    WHERE EXISTS (
        SELECT 1
        FROM salary_records s
        WHERE s.employee_id = p.employee_id
          AND s.effective_from >= p.promotion_date
          AND s.effective_from = (
              SELECT MIN(s2.effective_from)
              FROM salary_records s2
              WHERE s2.employee_id = p.employee_id
                AND s2.effective_from >= p.promotion_date
          )
          AND EXISTS (
              SELECT 1
              FROM compensation_bands b
              WHERE b.band_id = s.band_id
                AND (
                    b.role_id != p.new_role_id
                    OR b.level_id != p.new_level_id
                )
          )
    )
""")
print("Post-promotion role/level mismatches:", cur.fetchone()[0])

# Promotions with no salary history before or after promotion
cur.execute("""
    SELECT COUNT(*)
    FROM promotions p
    WHERE NOT EXISTS (
        SELECT 1
        FROM salary_records s
        WHERE s.employee_id = p.employee_id
          AND s.effective_from < p.promotion_date
    )
""")
print("Promotions without prior salary history:", cur.fetchone()[0])

cur.execute("""
    SELECT COUNT(*)
    FROM promotions p
    WHERE NOT EXISTS (
        SELECT 1
        FROM salary_records s
        WHERE s.employee_id = p.employee_id
          AND s.effective_from >= p.promotion_date
    )
""")
print("Promotions without subsequent salary history:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM promotions")
print("Total promotions:", cur.fetchone()[0])

con.close()
print("\nPROMOTION HISTORY AUDIT COMPLETED!")

