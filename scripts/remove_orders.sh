#!/bin/bash

# Check if a payment intent ID argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 PAYMENT_INTENT_ID"
    echo "Example: $0 pi_3O4X2K..."
    exit 1
fi

PAYMENT_INTENT_ID=$1
DB_PATH="instance/lunch.db"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file not found at $DB_PATH"
    exit 1
fi

# First show the orders that will be deleted
echo "The following orders will be deleted:"
echo "----------------------------------------"

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

# Ask for confirmation
read -p "Are you sure you want to delete these orders? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Delete the orders and show changes in the same transaction
    sqlite3 "$DB_PATH" << EOF
    DELETE FROM orders 
    WHERE payment_intent_id = '$PAYMENT_INTENT_ID';
    SELECT 'Deleted ' || changes() || ' order(s).' AS Result;
EOF
    
    if [ $? -eq 0 ]; then
        echo "Orders successfully deleted."
    else
        echo "Error: Failed to delete orders"
        exit 1
    fi
else
    echo "Operation cancelled"
    exit 0
fi 
