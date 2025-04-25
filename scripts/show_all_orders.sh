#!/bin/bash

# Set default DB_PATH only if not already set
: ${DB_PATH:="lunch.db"}

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file not found at $DB_PATH"
    exit 1
fi

echo "Showing all orders..."
echo "----------------------------------------"

# Query the database for all orders
sqlite3 "$DB_PATH" <<EOF
.mode column
.headers on
SELECT 
    orders.id as "Order ID",
    users.username as "User",
    orders.date as "Date",
    orders.meal_name as "Meal",
    orders.payment_intent_id as "Payment Intent ID"
FROM orders 
JOIN users ON orders.user_id = users.id
ORDER BY orders.date DESC, users.username;
EOF

if [ $? -ne 0 ]; then
    echo "Error: Failed to query the database"
    exit 1
fi

echo "----------------------------------------" 