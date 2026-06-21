# Pre-Implementation Investigation Protocol

Run this BEFORE writing any script or migration that touches production data, performs spatial joins, or relies on cross-table relationships.

## Purpose

Catch schema mismatches, data format surprises, timeout risks, and mapping bugs BEFORE implementation — not at runtime after 30 minutes of wasted execution.

## When to Run

- Any new ETL/build script
- Any migration that joins multiple tables
- Any batch operation on >1000 rows
- Any spatial query against production PostGIS
- Any cross-system integration (e.g., DCP slugs ↔ overlay LGA names)

## Protocol Steps

### Step 1: Schema Discovery

For EVERY table the script will read or write:

```sql
-- Column names and types (never assume)
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = '<table>'
ORDER BY ordinal_position;

-- Sample 5 real rows (never assume data format)
SELECT * FROM <table> WHERE <scope_filter> LIMIT 5;
```

**Output**: List of actual columns, types, and sample values. Flag any field that's text when you expected numeric, NULL when you expected populated, or contains embedded units/labels.

### Step 2: Value Audit (Join Keys)

For EVERY column used as a join key or filter:

```sql
-- Both sides of the join
SELECT DISTINCT <key_col> FROM <left_table> WHERE <scope> ORDER BY 1 LIMIT 30;
SELECT DISTINCT <key_col> FROM <right_table> WHERE <scope> ORDER BY 1 LIMIT 30;
```

**Output**: Side-by-side comparison. Flag any naming mismatches (underscore vs hyphen, case differences, merged-entity slugs, abbreviations).

### Step 3: Timeout Risk Assessment

For the HEAVIEST query in the planned script:

```sql
SET statement_timeout = '120000';  -- Supabase Pro hard limit
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
<your_query LIMIT 100>;
```

**Output**: Execution time extrapolated to full dataset. If >60s, the query MUST be batched. If spatial join, check GIST index exists on geometry columns.

### Step 4: Loop Invariant Check

For any batch/while loop:

Answer these questions IN WRITING before coding:
1. What marks a row as "processed"? (Column name, value)
2. What happens if the operation produces NULL/no-op for a row?
3. Does the row still exit the "pending" set after NULL result?
4. What's the maximum iterations? Is there a safety cap?

If question 3 is "no" → you have an infinite loop. Fix the sentinel.

### Step 5: Entity Name Mapping

If two systems reference the same entity (e.g., LGA):

```sql
-- System A's vocabulary
SELECT DISTINCT <entity_col> FROM <table_a> ORDER BY 1;
-- System B's vocabulary  
SELECT DISTINCT <entity_col> FROM <table_b> ORDER BY 1;
```

**Output**: Complete mapping table. Flag any entity in A that has no match in B. Build explicit mapping dict for non-obvious mappings (merged councils, name variants, abbreviations).

### Step 6: Numeric Parsing Check

For any column that feeds a typed model (pydantic, zod):

```sql
-- Check for non-numeric values in "numeric" fields
SELECT DISTINCT <col>
FROM <table>
WHERE <col> !~ '^\d+\.?\d*$'
  AND <col> IS NOT NULL
LIMIT 20;
```

**Output**: Any text values that won't parse as float/int. Build parser or reject before model validation.

## Report Format

Present ALL findings before writing any code:

```
## Pre-Implementation Investigation: <task name>

### Schema Discovery
- [table]: [columns discovered, any surprises]

### Value Audit
- [join key]: [matches/mismatches found]

### Timeout Risk
- Heaviest query: [estimated time] → [batch strategy if >60s]

### Loop Invariant
- Sentinel: [column = value]
- NULL-safe: [yes/no, fix if no]

### Name Mapping
- [entity]: [mapping table, N explicit overrides needed]

### Numeric Parsing
- [column]: [clean/needs parser]

### GO/NO-GO
- [ ] All schemas confirmed
- [ ] All join keys match
- [ ] Timeout risk mitigated
- [ ] Loop invariant is safe
- [ ] Name mappings complete
- [ ] Numeric formats validated

**Proceed with implementation: YES / NO (fix X first)**
```

## Marker File (REQUIRED — enables the PreToolUse hook gate)

After completing the investigation and confirming GO, write this marker file:

```bash
# Write to the project's .claude/ directory
cat > .claude/.pre-impl-done.json << 'EOF'
{
  "status": "passed",
  "timestamp": "<ISO timestamp>",
  "target": "<description of what was investigated>",
  "findings_summary": "<one-line summary of key discoveries>"
}
EOF
```

This file is checked by the `pre-impl-gate.js` hook. Without it, Edit/Write to scripts/, migrations/, services/ will be BLOCKED.

For trivial changes (invoked with `--trivial`):

```bash
cat > .claude/.pre-impl-done.json << 'EOF'
{
  "status": "trivial",
  "timestamp": "<ISO timestamp>",
  "reason": "<why this is trivial — e.g. 'fixing typo in comment, no logic change'>"
}
EOF
```

## Usage

- `/pre-impl` — full investigation before DB-touching work
- `/pre-impl --trivial` — skip investigation for genuinely trivial changes (comment, typo, import reorder)
