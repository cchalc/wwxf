# Databricks notebook source
# MAGIC %run ../resources/setup

# COMMAND ----------

# MAGIC %pip install /dbfs/databricks/libraries/pyrasterframes-0.10.1.dev0+dbr7.3-py3-none-any.whl

# COMMAND ----------

import pyrasterframes
from pyrasterframes.utils import create_rf_spark_session
spark = create_rf_spark_session()

# COMMAND ----------

# DBTITLE 1,Imports for Raster Frames
from pyrasterframes import rf_ipython
from pyrasterframes.utils import create_rf_spark_session
from pyspark.sql.functions import lit 
from pyrasterframes.rasterfunctions import *

# Use the provided convenience function to create a basic local SparkContext
spark = create_rf_spark_session()

# COMMAND ----------

# MAGIC %md
# MAGIC # Read data

# COMMAND ----------

# MAGIC %fs ls /mnt/bronze

# COMMAND ----------

# MAGIC %md 
# MAGIC ## weather station

# COMMAND ----------

weather_station = (spark.read
                   .option("inferSchema", True)
                   .option("delimiter", ",")
                   .option("header", True)
                   .csv(f"{bronze_path}/weather_station")
                  )
display(weather_station)

# COMMAND ----------

print(weather_station.printSchema())

# COMMAND ----------

# MAGIC %md
# MAGIC ## RDPS PR

# COMMAND ----------


