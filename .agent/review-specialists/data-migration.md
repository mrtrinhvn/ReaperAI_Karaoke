# Data Migration Review Specialist Checklist

> Scope: Khi diff chứa database schema changes, migration files, hoặc data transformation logic.
> Output: Structured findings với severity, confidence, path, category, summary, fix.

---

## Categories

### Schema Safety
- Column drop without checking for dependent queries/views
- Column type change that could lose precision (float→int, text→varchar(50))
- NOT NULL constraint added without default value for existing rows
- Missing down/rollback migration
- Index creation on large table without CONCURRENTLY (PostgreSQL)

### Data Integrity
- Foreign key added without verifying referential integrity of existing data
- Unique constraint that would fail on existing duplicate rows
- Enum type change without handling existing values
- Charset/collation change that could corrupt Unicode data

### Migration Order
- Migration depends on code changes being deployed first
- Multiple migrations that must run in strict order without explicit dependency
- Migration references table/column from another pending migration

### Backfill Safety
- Large table UPDATE without batching (locks entire table)
- Backfill script without progress reporting
- Missing idempotency — re-running causes duplicates
- No way to verify backfill completed successfully

### Rollback Planning
- Schema change that cannot be rolled back without data loss
- Missing verification step after migration
- No documented rollback procedure for data changes
