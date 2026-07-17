Acceptance Criteria 
1) Time Travel Proof 
((.venv) ) 
gaurav.bhatt@YTK-LAP-112 MINGW64 /d/retail_lakehouse_migration_and_conversational_query_assistant (main)
$ docker compose exec backend python -m spark_jobs.time_travel
time="2026-07-17T07:57:38+05:45" level=warning msg="D:\\retail_lakehouse_migration_and_conversational_query_assistant\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
/usr/local/lib/python3.12/site-packages/pyspark/bin/load-spark-env.sh: line 68: ps: command not found
Picked up JAVA_TOOL_OPTIONS: -XX:+UseContainerSupport -XX:MaxRAMPercentage=50.0 -XX:+UseG1GC
Picked up JAVA_TOOL_OPTIONS: -XX:+UseContainerSupport -XX:MaxRAMPercentage=50.0 -XX:+UseG1GC
26/07/17 02:12:40 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
Setting default log level to "WARN".
To adjust logging level use sc.setLogLevel(newLevel). For SparkR, use setLogLevel(newLevel).
=== SNAPSHOT HISTORY BEFORE CHANGE ===
+-------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|snapshot_id        |committed_at           |summary                                                                                                                                              
                                                                                                                                                                     |
+-------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|3873399174301443112|2026-07-15 09:17:20.833|{spark.app.id -> local-1784106997819, added-data-files -> 730, added-records -> 1200000, added-files-size -> 19610353, changed-partition-count -> 730, total-records -> 1200000, total-files-size -> 19610353, total-data-files -> 730, total-delete-files -> 0, total-position-deletes -> 0, total-equality-deletes -> 0}|
+-------------------+-----------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

SNAP_BEFORE=3873399174301443112
Inserted order_id=8888888 with discount_pct=0.05
SNAP_AFTER=5137975962802803442
=== CURRENT (latest snapshot) ===
26/07/17 02:12:58 WARN GarbageCollectionMetrics: To enable non-built-in garbage collector(s) List(G1 Concurrent GC), users should configure it(them) to spark.eventLog.gcMetrics.youngGenerationGarbageCollectors or spark.eventLog.gcMetrics.oldGenerationGarbageCollectors
+---------+-------------------+
|row_count|              total|
+---------+-------------------+
|  1200001|1.665838790520001E9|
+---------+-------------------+

=== AS OF SNAP_BEFORE (snapshot 3873399174301443112) ===
+---------+--------------------+
|row_count|               total|
+---------+--------------------+
|  1200000|1.6658386905300007E9|
+---------+--------------------+

=== AS OF TIMESTAMP 2026-07-15 09:17:20.833000 ===
+---------+
|row_count|
+---------+
|  1200000|
+---------+

![Time Travel Proof](time_travel_proof.png)

3) Partition Pruning Proof 
((.venv) )
gaurav.bhatt@YTK-LAP-112 MINGW64 /d/retail_lakehouse_migration_and_conversational_query_assistant (main)
$ docker compose exec backend python -m spark_jobs.prove_pruning
time="2026-07-17T07:47:55+05:45" level=warning msg="D:\\retail_lakehouse_migration_and_conversational_query_assistant\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
/usr/local/lib/python3.12/site-packages/pyspark/bin/load-spark-env.sh: line 68: ps: command not found
Picked up JAVA_TOOL_OPTIONS: -XX:+UseContainerSupport -XX:MaxRAMPercentage=50.0 -XX:+UseG1GC
Picked up JAVA_TOOL_OPTIONS: -XX:+UseContainerSupport -XX:MaxRAMPercentage=50.0 -XX:+UseG1GC
26/07/17 02:02:58 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
Setting default log level to "WARN".
To adjust logging level use sc.setLogLevel(newLevel). For SparkR, use setLogLevel(newLevel).
=== FULL SCAN (no filter) ===
== Parsed Logical Plan ==
'Project [unresolvedalias('SUM('total_amount), None)]
+- 'UnresolvedRelation [nessie, retail, fact_sales], [], false

== Analyzed Logical Plan ==
sum(total_amount): double
Aggregate [sum(total_amount#7) AS sum(total_amount)#9]
+- SubqueryAlias nessie.retail.fact_sales
   +- RelationV2[order_id#0L, order_date#1, product_id#2L, store_id#3L, customer_id#4L, quantity#5, unit_price#6, total_amount#7] nessie.retail.fact_sales nessie.retail.fact_sales

== Optimized Logical Plan ==
Aggregate [sum(total_amount#7) AS sum(total_amount)#9]
+- RelationV2[total_amount#7] nessie.retail.fact_sales

== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- HashAggregate(keys=[], functions=[sum(total_amount#7)], output=[sum(total_amount)#9])
   +- Exchange SinglePartition, ENSURE_REQUIREMENTS, [plan_id=11]
      +- HashAggregate(keys=[], functions=[partial_sum(total_amount#7)], output=[sum#18])
         +- BatchScan nessie.retail.fact_sales[total_amount#7] nessie.retail.fact_sales (branch=null) [filters=, groupedBy=] RuntimeFilters: []

=== PRUNED (January 2024 only) ===
== Parsed Logical Plan ==
'Project [unresolvedalias('SUM('total_amount), None)]
+- 'Filter (('order_date >= 2024-01-01) AND ('order_date <= 2024-01-31))
   +- 'UnresolvedRelation [nessie, retail, fact_sales], [], false

== Analyzed Logical Plan ==
sum(total_amount): double
Aggregate [sum(total_amount#26) AS sum(total_amount)#33]
+- Filter ((order_date#20 >= cast(2024-01-01 as date)) AND (order_date#20 <= cast(2024-01-31 as date)))
   +- SubqueryAlias nessie.retail.fact_sales
      +- RelationV2[order_id#19L, order_date#20, product_id#21L, store_id#22L, customer_id#23L, quantity#24, unit_price#25, total_amount#26] nessie.retail.fact_sales nessie.retail.fact_sales    

== Optimized Logical Plan ==
Aggregate [sum(total_amount#26) AS sum(total_amount)#33]
+- Project [total_amount#26]
   +- RelationV2[order_date#20, total_amount#26] nessie.retail.fact_sales

== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- HashAggregate(keys=[], functions=[sum(total_amount#26)], output=[sum(total_amount)#33])
   +- Exchange SinglePartition, ENSURE_REQUIREMENTS, [plan_id=26]
      +- HashAggregate(keys=[], functions=[partial_sum(total_amount#26)], output=[sum#38])
         +- Project [total_amount#26]
            +- BatchScan nessie.retail.fact_sales[order_date#20, total_amount#26] nessie.retail.fact_sales (branch=null) [filters=order_date IS NOT NULL, order_date >= 19723, order_date <= 19753, groupedBy=] RuntimeFilters: []

   +- Exchange SinglePartition, ENSURE_REQUIREMENTS, [plan_id=26]
      +- HashAggregate(keys=[], functions=[partial_sum(total_amount#26)], output=[sum#38])
         +- Project [total_amount#26]
            +- BatchScan nessie.retail.fact_sales[order_date#20, total_amount#26] nessie.retail.fact_sales (branch=null) [filters=order_date IS NOT NULL, order_date >= 19723, order_date <= 19753, groupedBy=] RuntimeFilters: []
   +- Exchange SinglePartition, ENSURE_REQUIREMENTS, [plan_id=26]
      +- HashAggregate(keys=[], functions=[partial_sum(total_amount#26)], output=[sum#38])
         +- Project [total_amount#26]
            +- BatchScan nessie.retail.fact_sales[order_date#20, total_amount#26] nessie.retail.fact_sales (branch=null) [filters=order_date IS NOT NULL, order_date >= 19723, order_date <= 19753   +- Exchange SinglePartition, ENSURE_REQUIREMENTS, [plan_id=26]
      +- HashAggregate(keys=[], functions=[partial_sum(total_amount#26)], output=[sum#38])
         +- Project [total_amount#26]
   +- Exchange SinglePartition, ENSURE_REQUIREMENTS, [plan_id=26]
   +- Exchange SinglePartition, ENSURE_REQUIREMENTS, [plan_id=26]
      +- HashAggregate(keys=[], functions=[partial_sum(total_amount#26)], output=[sum#38])
         +- Project [total_amount#26]
            +- BatchScan nessie.retail.fact_sales[order_date#20, total_amount#26] nessie.retail.fact_sales (branch=null) [filters=order_date IS NOT NULL, order_date >= 19723, order_date <= 19753, groupedBy=] RuntimeFilters: []

=== FILE COUNTS (from Iceberg metadata) ===
26/07/17 02:03:12 WARN GarbageCollectionMetrics: To enable non-built-in garbage collector(s) List(G1 Concurrent GC), users should configure it(them) to spark.eventLog.gcMetrics.youngGenerationGarbageCollectors or spark.eventLog.gcMetrics.oldGenerationGarbageCollectors
+-----------+
|total_files|
+-----------+
|        730|
+-----------+

+------------+
|pruned_files|
+------------+
|          31|
+------------+


















->spark_session.py:
A few notes on what changed:

JAR_DIR defaults to your existing Ivy cache path but can be overridden with the SPARK_JAR_DIR env var, so it's portable if this ever runs on a different machine or in CI.
_resolve_jars() globs recursively for all .jar files in that folder and raises a clear error if it comes up empty, rather than letting Spark fail with a cryptic classpath error.
Added spark.stop() in the __main__ block, per the earlier fix, so you don't get the dangling-process taskkill output.

One thing to double check: globbing your entire .ivy2\jars folder pulls in every jar Ivy has ever cached, not just the two you need — if you've used spark.jars.packages for other projects before, you might pick up unrelated or conflicting jar versions. If you hit classpath weirdness, it's worth pruning JAR_DIR down to a dedicated folder with just the Iceberg/Nessie jars (and their transitive deps) copied in.

-> When running PySpark locally (not via spark-submit --driver-memory), the JVM is launched by py4j the moment getOrCreate() is called — but spark.driver.memory (and any driver-JVM-level setting) must be known before that JVM boots. Setting .config("spark.driver.memory", "4g") in your Python builder chain is a config that gets sent to the SparkConf, but in local/client mode the driver runs inside the same JVM that py4j already started — so by the time your .config() call happens, the JVM's heap size is already fixed at whatever the default was. Spark's own docs explicitly call this out: driver memory can't be set through SparkConf in your application code for client/local mode — it silently does nothing, which is exactly what you're seeing.
Fix: Set it through an environment variable before the JVM starts, not through .config(). In your Git Bash terminal


$ python -m spark_jobs.ingest
Setting default log level to "WARN".
To adjust logging level use sc.setLogLevel(newLevel). For SparkR, use setLogLevel(newLevel).
Loaded dim_product
Loaded dim_date
Loaded dim_store
26/07/03 14:05:27 WARN GarbageCollectionMetrics: To enable non-built-in garbage collector(s) List(G1 Concurrent GC), users should configure it(them) to spark.eventLog.gcMetrics.youngGenerationGarbageCollectors or spark.eventLog.gcMetrics.oldGenerationGarbageCollectors
Loaded dim_customer
Loaded fact_sales
SNAPSHOT_ID=4289988203811864975
+--------+
|count(1)|
+--------+
| 1200000|
+--------+

## Partition Pruning Proof

### Full scan (no filter)
BatchScan nessie.retail.fact_sales[total_amount#7] ... [filters=, groupedBy=]

### Pruned scan (January 2024 filter)
BatchScan nessie.retail.fact_sales[order_date#20, total_amount#26] ...
[filters=order_date IS NOT NULL, order_date >= 19723, order_date <= 19753, groupedBy=]

### File counts (from Iceberg's `fact_sales.files` metadata table)
| Query                  | Files touched |
|-------------------------|---------------|
| Full scan (no filter)   | 730           |
| Pruned (Jan 2024 only)  | 31            |

Iceberg's hidden `days(order_date)` partition transform lets the query planner push the date filter down to file-level pruning without needing an explicit partition column in the WHERE clause — confirmed by the drop from 730 files to 31 files (~4% of the table scanned).

## Issue Log

### 1. Nessie catalog lost state on every restart

**Problem:** The Nessie server was running with its default in-memory version store, and the Iceberg warehouse was configured to write to `file:///tmp/iceberg_warehouse`, which Windows resolves to `AppData\Local\Temp`. Any container restart wiped Nessie's catalog (`SHOW DATABASES IN nessie` returned empty), and the underlying Parquet/metadata files in the Windows temp directory were also gone — a full reset with no recovery path.

**Root cause:** Two separate issues compounding:
- Nessie's Docker image (`projectnessie/nessie:0.76.0`) defaults to `VERSION_STORE_TYPE=IN_MEMORY`, which never persists to disk.
- The Iceberg warehouse path pointed at genuinely temporary OS storage, subject to cleanup at any time.

**Fix:**
- Added a `postgres` database (`nessie`) to the existing Postgres container and configured Nessie to use it as a JDBC-backed version store, since RocksDB isn't a supported store type in the official Nessie image (confirmed via the `Installed features` line in the startup logs — only `jdbc-postgresql`, `mongodb-client`, `amazon-dynamodb`, `cassandra-client`, and `google-cloud-bigtable` are available).
- Updated `spark_session.py` to point `spark.sql.catalog.nessie.warehouse` at a durable path on the project drive instead of `/tmp`.

**Verification:** Ran `docker compose restart nessie`, then re-queried `SHOW TABLES IN nessie.retail` — all five tables (`dim_product`, `dim_date`, `dim_store`, `dim_customer`, `fact_sales`) persisted across the restart, confirming the fix.

---

### 2. `CAST` required for date literals in `schema_evolution.py`

**Problem:** The `INSERT INTO ... VALUES (..., '2024-06-15', ...)` statement failed with:
```
AnalysisException: [INCOMPATIBLE_DATA_FOR_TABLE.CANNOT_SAFELY_CAST] Cannot safely cast `order_date` "STRING" to "DATE".
```

**Root cause:** Under Spark's ANSI type-checking mode, a bare string literal in an `INSERT ... VALUES` is typed as `STRING`, and Spark will not implicitly widen it to `DATE` for an unsafe cast — unlike older Spark versions, which allowed this coercion silently.

**Fix:** Explicitly cast the literal:
```sql
INSERT INTO nessie.retail.fact_sales
VALUES (9999999, CAST('2024-06-15' AS DATE), 1, 1, 1, 2, 49.99, 99.98, 0.10)
```

---

## Partition & Schema Evolution Proofs

### Schema Evolution via Field IDs

**Before adding `discount_pct`:**
```
+--------------+----------------+
|      col_name|       data_type|
+--------------+----------------+
|      order_id|          bigint|
|    order_date|            date|
|    product_id|          bigint|
|      store_id|          bigint|
|   customer_id|          bigint|
|      quantity|             int|
|    unit_price|          double|
|  total_amount|          double|
+--------------+----------------+
```

**After `ALTER TABLE ... ADD COLUMN discount_pct DOUBLE`, querying pre-existing rows:**
```
+--------+------------+------------+
|order_id|total_amount|discount_pct|
+--------+------------+------------+
|    1001|      158.55|        NULL|
|    1554|      1892.8|        NULL|
|    2407|     1335.15|        NULL|
|    2553|       489.3|        NULL|
|    3507|      2053.1|        NULL|
+--------+------------+------------+
```
Old data files have no `discount_pct` column on disk at all — Iceberg resolves it as `NULL` via Field ID mapping rather than erroring or misaligning columns by position.

**After inserting a new row with `discount_pct` populated, comparing old vs. new:**
```
+--------+------------+
|order_id|discount_pct|
+--------+------------+
| 9999999|         0.1|
|       1|        NULL|
+--------+------------+
```

This confirms Iceberg's schema evolution model: old rows (`order_id=1`) and new rows (`order_id=9999999`) coexist under a single evolved schema, with no rewrite of historical data files required.

## Concurrent Writer Conflict (Optimistic Concurrency Control)

Iceberg uses optimistic concurrency: two writers appending to the same partition simultaneously will produce a `CommitFailedException` when the second writer tries to commit against a stale catalog state. On Linux, this is straightforward — two threads each hold their own Spark session and write concurrently. On Windows, PySpark is not thread-safe (threading crashes the Python worker) and multiprocessing hits the same issue because PySpark's JVM bridge doesn't survive process forking. Subprocess isolation via `subprocess.Popen` avoids the crash — each process gets its own JVM — but SQL INSERT is atomic and fast enough that both commits complete sequentially before either can conflict. The conflict simulation therefore requires either a Linux host (where threading works) or manual seeding of the `nessie.retail.commit_conflicts` metadata table. The `get_commit_conflicts` agent tool reads from this table regardless of how the records were produced.

```bash
.venv\Scripts\python -m spark_jobs.seed_conflicts
```

---

## Time Travel Proof

Iceberg records every write as an immutable snapshot. The same query run against two different snapshots of `fact_sales` returns different results, proving real historical state is preserved — not just current-state metadata.

| Snapshot                                      | COUNT(*)  | SUM(total_amount)     |
|------------------------------------------------|-----------|-------------------------|
| Current (latest, snapshot `5631275555345608`)   | 1,200,002 | 1,665,838,890.50        |
| AS OF SNAP_BEFORE (snapshot `1711499913188484340`) | 1,200,000 | 1,665,838,690.53     |

The extra 2 rows and the total difference come from two inserts made after `SNAP_BEFORE`: one during the schema evolution demo (Task 6) and one made in this task to create `SNAP_AFTER`.

### Time travel by timestamp

Iceberg also supports `TIMESTAMP AS OF`, resolving to whichever snapshot was current at a given commit time (not to be confused with any date column inside the data, like `order_date`):

```sql
SELECT COUNT(*) FROM nessie.retail.fact_sales
TIMESTAMP AS OF '2026-07-06 09:59:00.678'
```

Result: `1,200,000` rows — matching `SNAP_BEFORE` exactly, confirming both time-travel mechanisms (`VERSION AS OF` and `TIMESTAMP AS OF`) resolve to the same consistent historical state.

Full snapshot history, including deletes, is visible via:
```sql
SELECT snapshot_id, committed_at, summary
FROM nessie.retail.fact_sales.snapshots
ORDER BY committed_at
```