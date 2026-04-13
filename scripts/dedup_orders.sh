#!/bin/bash
# Removes duplicate (user_id, date) order rows from the database, keeping the
# row with the lowest id.  Run this once against the production database before
# deploying the UniqueConstraint migration.

: ${DB_PATH:="lunch.db"}

if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file not found at $DB_PATH"
    exit 1
fi

echo "Checking for duplicate orders in $DB_PATH ..."

COUNT=$(sqlite3 "$DB_PATH" "
SELECT COUNT(*) FROM orders
WHERE id NOT IN (
    SELECT MIN(id) FROM orders GROUP BY user_id, date
);")

if [ "$COUNT" -eq 0 ]; then
    echo "No duplicate orders found. Nothing to do."
    exit 0
fi

echo "Found $COUNT duplicate row(s) to remove."
echo "Removing duplicates (keeping earliest order id per user+date)..."

sqlite3 "$DB_PATH" "
DELETE FROM orders
WHERE id NOT IN (
    SELECT MIN(id) FROM orders GROUP BY user_id, date
);"

if [ $? -ne 0 ]; then
    echo "Error: Failed to remove duplicates."
    exit 1
fi

echo "Done. $COUNT duplicate row(s) removed."
