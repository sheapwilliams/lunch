#!/bin/bash

SHOW_PAYMENT_INTENT=false

# Parse flags
while getopts "p" opt; do
    case $opt in
        p) SHOW_PAYMENT_INTENT=true ;;
        \?) echo "Usage: $0 [-p] YYYY-MM-DD"; exit 1 ;;
    esac
done
shift $((OPTIND - 1))

# Check for date argument
if [ $# -ne 1 ]; then
    echo "Usage: $0 [-p] YYYY-MM-DD"
    echo "  -p  Include payment intent ID next to each order"
    echo "Example: $0 2024-03-20"
    echo "         $0 -p 2024-03-20"
    exit 1
fi

DATE=$1

# Validate date format
if ! [[ $DATE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "Error: Invalid date format. Please use YYYY-MM-DD"
    exit 1
fi

# Path to the SQLite database
: ${DB_PATH:="instance/lunch.db"}

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file not found at $DB_PATH"
    exit 1
fi

echo "Orders for $DATE:"
echo "----------------------------------------"

if $SHOW_PAYMENT_INTENT; then
    sqlite3 "$DB_PATH" << EOF
.mode column
.headers on
SELECT
    users.username as User,
    orders.meal_name as "Meal Order",
    orders.payment_intent_id as "Payment Intent"
FROM orders
JOIN users ON orders.user_id = users.id
WHERE date(orders.date) = date('$DATE')
ORDER BY users.username;
EOF
else
    sqlite3 "$DB_PATH" << EOF
.mode column
.headers on
SELECT
    users.username as User,
    orders.meal_name as "Meal Order"
FROM orders
JOIN users ON orders.user_id = users.id
WHERE date(orders.date) = date('$DATE')
ORDER BY users.username;
EOF
fi

echo "----------------------------------------"
echo "Summary:"
echo "----------------------------------------"

# Query the database for order summary
sqlite3 "$DB_PATH" << EOF
.mode column
.headers on
SELECT
    meal_name as "Meal",
    COUNT(*) as "Count"
FROM orders
WHERE date(date) = date('$DATE')
GROUP BY meal_name
ORDER BY COUNT(*) DESC;
EOF

# Check if any orders were found
if [ $? -ne 0 ]; then
    echo "Error: Failed to query the database"
    exit 1
fi

echo "----------------------------------------"
