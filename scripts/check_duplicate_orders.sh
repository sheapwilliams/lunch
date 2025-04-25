#!/bin/bash

: ${DB_PATH:="lunch.db"}

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file not found at $DB_PATH"
    exit 1
fi

echo "Checking for duplicate orders..."
echo "----------------------------------------"

# Query the database for duplicate orders
sqlite3 "$DB_PATH" <<EOF
.mode column
.headers on
SELECT 
    users.username as "User",
    orders.date as "Date",
    orders.meal_name as "Meal",
    COUNT(*) as "Count",
    GROUP_CONCAT(orders.id) as "Order IDs"
FROM orders 
JOIN users ON orders.user_id = users.id
GROUP BY users.username, orders.date, orders.meal_name
HAVING COUNT(*) > 1
ORDER BY users.username, orders.date;
EOF

# Check if any duplicates were found
if [ $? -ne 0 ]; then
    echo "Error: Failed to query the database"
    exit 1
fi

echo "----------------------------------------"
echo "Detailed view of duplicate orders:"
echo "----------------------------------------"

# Show detailed information for each duplicate order
sqlite3 "$DB_PATH" <<EOF
.mode column
.headers on
WITH duplicates AS (
    SELECT 
        users.username,
        orders.date,
        orders.meal_name,
        COUNT(*) as count
    FROM orders 
    JOIN users ON orders.user_id = users.id
    GROUP BY users.username, orders.date, orders.meal_name
    HAVING COUNT(*) > 1
)
SELECT 
    users.username as "User",
    orders.date as "Date",
    orders.meal_name as "Meal",
    orders.id as "Order ID",
    orders.payment_intent_id as "Payment Intent ID"
FROM orders 
JOIN users ON orders.user_id = users.id
JOIN duplicates ON 
    users.username = duplicates.username AND
    orders.date = duplicates.date AND
    orders.meal_name = duplicates.meal_name
ORDER BY users.username, orders.date, orders.id;
EOF

echo "----------------------------------------"
