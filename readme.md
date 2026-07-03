->spark_session.py:
A few notes on what changed:

JAR_DIR defaults to your existing Ivy cache path but can be overridden with the SPARK_JAR_DIR env var, so it's portable if this ever runs on a different machine or in CI.
_resolve_jars() globs recursively for all .jar files in that folder and raises a clear error if it comes up empty, rather than letting Spark fail with a cryptic classpath error.
Added spark.stop() in the __main__ block, per the earlier fix, so you don't get the dangling-process taskkill output.

One thing to double check: globbing your entire .ivy2\jars folder pulls in every jar Ivy has ever cached, not just the two you need — if you've used spark.jars.packages for other projects before, you might pick up unrelated or conflicting jar versions. If you hit classpath weirdness, it's worth pruning JAR_DIR down to a dedicated folder with just the Iceberg/Nessie jars (and their transitive deps) copied in.

-> When running PySpark locally (not via spark-submit --driver-memory), the JVM is launched by py4j the moment getOrCreate() is called — but spark.driver.memory (and any driver-JVM-level setting) must be known before that JVM boots. Setting .config("spark.driver.memory", "4g") in your Python builder chain is a config that gets sent to the SparkConf, but in local/client mode the driver runs inside the same JVM that py4j already started — so by the time your .config() call happens, the JVM's heap size is already fixed at whatever the default was. Spark's own docs explicitly call this out: driver memory can't be set through SparkConf in your application code for client/local mode — it silently does nothing, which is exactly what you're seeing.
Fix: Set it through an environment variable before the JVM starts, not through .config(). In your Git Bash terminal