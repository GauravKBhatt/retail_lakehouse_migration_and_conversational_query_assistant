import os
import numpy as np
import pandas as pd
from datetime import date, timedelta

np.random.seed(99)

START_DATE = date(2025, 1, 1)
NUM_DAYS = 730
PRODUCTS = 500
STORES = 50
CUSTOMERS = 100_000
ROWS_PER_BATCH = 100_000
NUM_BATCHES = 5
BASE_ORDER_ID = 2_000_001

os.makedirs("data", exist_ok=True)

for batch in range(1, NUM_BATCHES + 1):
    n = ROWS_PER_BATCH
    ids = range(BASE_ORDER_ID + (batch - 1) * n, BASE_ORDER_ID + batch * n)
    dates = [START_DATE + timedelta(days=int(x)) for x in np.random.randint(0, NUM_DAYS, n)]

    df = pd.DataFrame({
        "order_id": ids,
        "order_date": dates,
        "product_id": np.random.randint(1, PRODUCTS + 1, n),
        "store_id": np.random.randint(1, STORES + 1, n),
        "customer_id": np.random.randint(1, CUSTOMERS + 1, n),
        "quantity": np.random.randint(1, 11, n),
        "unit_price": np.round(np.random.uniform(5.0, 500.0, n), 2),
    })
    df["total_amount"] = np.round(df["quantity"] * df["unit_price"], 2)

    path = f"data/delta_batch_{batch}.csv"
    df.to_csv(path, index=False)
    print(f"Generated {path} ({n} rows)")

print("All delta batches generated.")