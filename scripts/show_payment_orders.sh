#!/bin/bash

# Check if a payment intent ID argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 PAYMENT_INTENT_ID"
    echo "Example: $0 pi_3O4X2K..."
    exit 1
fi

PAYMENT_INTENT_ID=$1
: ${DB_PATH:="instance/lunch.db"}

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file not found at $DB_PATH"
    exit 1
fi

echo "Orders for Payment Intent: $PAYMENT_INTENT_ID"
echo "----------------------------------------"

# Show detailed order information
sqlite3 "$DB_PATH" << EOF
.mode column
.headers on
SELECT 
    orders.date as "Date",
    users.username as "User",
    orders.meal_name as "Meal Order",
    orders.payment_intent_id as "Payment Intent"
FROM orders 
JOIN users ON orders.user_id = users.id 
WHERE orders.payment_intent_id = '$PAYMENT_INTENT_ID'
ORDER BY orders.date;
EOF

# Check if any orders were found
if [ $? -ne 0 ]; then
    echo "Error: Failed to query the database"
    exit 1
fi

echo "----------------------------------------"
echo "Summary:"
echo "----------------------------------------"

# Show summary of orders
sqlite3 "$DB_PATH" << EOF
.mode column
.headers on
SELECT 
    meal_name as "Meal",
    COUNT(*) as "Count"
FROM orders 
WHERE payment_intent_id = '$PAYMENT_INTENT_ID'
GROUP BY meal_name
ORDER BY COUNT(*) DESC;
EOF

# Show total number of orders
echo "----------------------------------------"
sqlite3 "$DB_PATH" << EOF
.mode column
.headers on
SELECT 
    COUNT(*) as "Total Orders",
    COUNT(DISTINCT user_id) as "Unique Users"
FROM orders 
WHERE payment_intent_id = '$PAYMENT_INTENT_ID';
EOF

echo "----------------------------------------" 
