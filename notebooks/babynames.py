# Databricks notebook source
from pyspark.sql.functions import rand, input_file_name, from_json, col
from pyspark.sql.types import *

# import mlflow
# import mlflow.spark
# from mlflow.utils.file_utils import TempDir

from time import sleep
import re
import seaborn as sn
import pandas as pd
import matplotlib.pyplot as plt

# COMMAND ----------

demo = "babynames"

def clean_string(a: str) -> str:
  return re.sub('[^A-Za-z0-9]+', '', a).lower()

# COMMAND ----------

user = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().get("user").get()
username = clean_string(user.partition('@')[0])
dbName = re.sub(r'\W+', '_', username) + "_" + demo
path = f"/Users/{user}/{demo}"
print(f"path (default path): {path}")
spark.sql("""create database if not exists {} LOCATION '{}/{}/tables' """.format(dbName, demo, path))
spark.sql("""USE {}""".format(dbName))
print("dbName (using database): {}".format(dbName))

# COMMAND ----------

babynames = spark.read.format("csv").option("header", "true").option("inferSchema", "true").load("dbfs:/FileStore/babynames.csv")
babynames.createOrReplaceTempView("babynames_table")
years = spark.sql("select distinct(Year) from babynames_table").rdd.map(lambda row : row[0]).collect()
years.sort()
dbutils.widgets.dropdown("year", "2014", [str(x) for x in years])
year = dbutils.widgets.get("year")

# COMMAND ----------

display(babynames
        .filter(babynames.Year == dbutils.widgets.get("year"))
        .withColumnRenamed("First Name", "First_Name")
       )

# COMMAND ----------

SILVER_PATH = f"dbfs:{path}/silver/{year}"
print(SILVER_PATH)

# COMMAND ----------

dbutils.fs.rm(path+"/silver", True)

# COMMAND ----------

# filtered_baby_names = (babynames
#                        .filter(babynames.Year == dbutils.widgets.get("year"))
#                        .withColumnRenamed("First Name", "First_Name")
#                        .write
#                        .format("parquet")
#                        .mode("overwrite")
#                        .save(SILVER_PATH)
#                       )

# spark.sql(f"CREATE TABLE babynames_{year} USING DELTA LOCATION '" + SILVER_PATH + "'")

# COMMAND ----------

filtered_baby_names = (babynames
                       .filter(babynames.Year == dbutils.widgets.get("year"))
                       .withColumnRenamed("First Name", "First_Name")
                       .write
                       .format("delta")
                       .mode("overwrite")
                       .option("path", SILVER_PATH)
                       .saveAsTable(f"babynames_{year}")
                      )

# COMMAND ----------


