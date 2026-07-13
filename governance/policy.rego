package lakehouse.masking

# Analysts see hashed customer_id, never raw
masked_columns[col] {
    input.role == "analyst"
    col := "customer_id"
}

# Non-admins cannot see lifetime value bucket
masked_columns[col] {
    input.role != "admin"
    col := "lifetime_value_bucket"
}

# Non-admins cannot see cost price (margin-sensitive)
masked_columns[col] {
    input.role != "admin"
    col := "cost_price"
}