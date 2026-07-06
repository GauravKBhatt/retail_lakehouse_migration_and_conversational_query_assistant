import os
from datetime import date, timedelta

import numpy as np
import pandas as pd

# Configuration

np.random.seed(42)

START_DATE = date(2023, 1, 1)
NUM_DAYS = 730

FACT_ROWS = 1_200_000
PRODUCTS = 500
STORES = 50
CUSTOMERS = 100_000

os.makedirs("data", exist_ok=True)

# Generate fact_sales.csv

dates = [
    START_DATE + timedelta(days=int(x))
    for x in np.random.randint(0, NUM_DAYS, FACT_ROWS)
]

fact_sales = pd.DataFrame(
    {
        "order_id": range(1, FACT_ROWS + 1),
        "order_date": dates,
        "product_id": np.random.randint(1, PRODUCTS + 1, FACT_ROWS),
        "store_id": np.random.randint(1, STORES + 1, FACT_ROWS),
        "customer_id": np.random.randint(1, CUSTOMERS + 1, FACT_ROWS),
        "quantity": np.random.randint(1, 11, FACT_ROWS),
        "unit_price": np.round(
            np.random.uniform(5.0, 500.0, FACT_ROWS), 2
        ),
    }
)

fact_sales["total_amount"] = np.round(
    fact_sales["quantity"] * fact_sales["unit_price"],
    2,
)

fact_sales.to_csv("fact_sales.csv", index=False)

print("Generated fact_sales.csv")

# Generate dim_date.csv

date_range = pd.date_range("2023-01-01", "2024-12-31")

dim_date = pd.DataFrame(
    {
        "date_id": range(1, len(date_range) + 1),
        "full_date": date_range.date,
        "year": date_range.year,
        "quarter": date_range.quarter,
        "month": date_range.month,
        "week": date_range.isocalendar().week.astype(int),
        "day_of_week": date_range.day_name(),
    }
)

dim_date.to_csv("dim_date.csv", index=False)

print("Generated dim_date.csv")

# Generate dim_product.csv

categories = {
    "Electronics": [
        "Phones",
        "Laptops",
        "Accessories",
    ],
    "Clothing": [
        "Men",
        "Women",
        "Kids",
    ],
    "Home": [
        "Kitchen",
        "Furniture",
        "Decor",
    ],
    "Sports": [
        "Fitness",
        "Outdoor",
        "Cycling",
    ],
    "Beauty": [
        "Skin Care",
        "Hair Care",
        "Cosmetics",
    ],
}

brands = [
    "Alpha",
    "Nova",
    "Prime",
    "Vertex",
    "Zen",
    "Apex",
    "Orbit",
    "Fusion",
]

products = []

for pid in range(1, PRODUCTS + 1):
    category = np.random.choice(list(categories.keys()))
    subcategory = np.random.choice(categories[category])

    products.append(
        {
            "product_id": pid,
            "name": f"Product {pid}",
            "category": category,
            "subcategory": subcategory,
            "brand": np.random.choice(brands),
            "cost_price": round(
                np.random.uniform(2.0, 300.0), 2
            ),
        }
    )

dim_product = pd.DataFrame(products)

dim_product.to_csv("dim_product.csv", index=False)

print("Generated dim_product.csv")

# Generate dim_store.csv

cities = [
    ("New York", "NY", "East"),
    ("Los Angeles", "CA", "West"),
    ("Chicago", "IL", "Midwest"),
    ("Houston", "TX", "South"),
    ("Phoenix", "AZ", "West"),
    ("Seattle", "WA", "West"),
    ("Boston", "MA", "East"),
    ("Miami", "FL", "South"),
]

store_types = [
    "Mall",
    "Outlet",
    "Flagship",
    "Express",
]

stores = []

for sid in range(1, STORES + 1):
    city, state, region = random_city = cities[np.random.randint(len(cities))]

    stores.append(
        {
            "store_id": sid,
            "name": f"Store {sid}",
            "city": city,
            "state": state,
            "region": region,
            "store_type": np.random.choice(store_types),
        }
    )

dim_store = pd.DataFrame(stores)

dim_store.to_csv("dim_store.csv", index=False)

print("Generated dim_store.csv")

# Generate dim_customer.csv

segments = [
    "Consumer",
    "Corporate",
    "Small Business",
]

lv_buckets = [
    "Low",
    "Medium",
    "High",
    "VIP",
]

join_dates = [
    START_DATE + timedelta(days=int(x))
    for x in np.random.randint(0, NUM_DAYS, CUSTOMERS)
]

dim_customer = pd.DataFrame(
    {
        "customer_id": range(1, CUSTOMERS + 1),
        "segment": np.random.choice(
            segments,
            CUSTOMERS,
            p=[0.65, 0.25, 0.10],
        ),
        "join_date": join_dates,
        "lifetime_value_bucket": np.random.choice(
            lv_buckets,
            CUSTOMERS,
            p=[0.35, 0.35, 0.20, 0.10],
        ),
    }
)

dim_customer.to_csv(
    "data/dim_customer.csv",
    index=False,
)

print("Generated dim_customer.csv")

print("\nAll datasets generated successfully.")