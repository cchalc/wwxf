# Databricks notebook source
# MAGIC %pip install /dbfs/databricks/libraries/pyrasterframes-0.10.1.dev0+dbr7.3-py3-none-any.whl

# COMMAND ----------

# MAGIC %run ../resources/setup

# COMMAND ----------

# import pyrasterframes
# from pyrasterframes.utils import create_rf_spark_session
# spark = create_rf_spark_session()

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import lit 
 
from pyrasterframes import *
from pyrasterframes.rasterfunctions import *
import pyrasterframes.rf_ipython
 
from pyrasterframes.utils import build_info, gdal_version
 
spark.withRasterFrames()

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
# MAGIC ## Example Raster

# COMMAND ----------

def scene(band):
    b = str(band).zfill(2) # converts int 2 to '02'
    return 'https://modis-pds.s3.amazonaws.com/MCD43A4.006/11/08/2019059/' \
             'MCD43A4.A2019059.h11v08.006.2019072203257_B{}.TIF'.format(b)
 
rf = spark.read.raster(scene(2), tile_dimensions=(256, 256))
sample_tile = rf.select(rf_tile('proj_raster').alias('tile')).first()['tile']
sample_tile

# COMMAND ----------

print(f"gdal version --> {gdal_version()}")
print(f"build_info --> {build_info()}")

# COMMAND ----------

# Construct a CSV "catalog" for RasterFrames `raster` reader. Catalogs can also be Spark or Pandas DataFrames.
bands = [f'B{b}' for b in [4, 5]]
uris = [f'https://landsat-pds.s3.us-west-2.amazonaws.com/c1/L8/014/032/LC08_L1TP_014032_20190720_20190731_01_T1/LC08_L1TP_014032_20190720_20190731_01_T1_{b}.TIF' for b in bands]
catalog = ','.join(bands) + '\n' + ','.join(uris)
 
# Read red and NIR bands from Landsat 8 dataset over NYC
rf = spark.read.raster(catalog, bands) \
    .withColumnRenamed('B4', 'red').withColumnRenamed('B5', 'NIR') \
    .withColumn('longitude_latitude', st_reproject(st_centroid(rf_geometry('red')), rf_crs('red'), lit('EPSG:4326'))) \
    .withColumn('NDVI', rf_normalized_difference('NIR', 'red')) \
    .where(rf_tile_sum('NDVI') > 10000)

# COMMAND ----------

df_results = rf.select('longitude_latitude', rf_tile('red'), rf_tile('NIR'), rf_tile('NDVI'))
print(f"`df_results` type? {type(df_results)}")
df_results

# COMMAND ----------

display(df_results)

# COMMAND ----------

# MAGIC %md
# MAGIC ## RDPS PR

# COMMAND ----------

# MAGIC %fs ls /mnt/bronze/rdps_pr

# COMMAND ----------

rf = spark.read.raster("dbfs:/mnt/bronze/rdps_pr/RDPS.ETA_PR-2021121500.tiff")
rf.printSchema()

# COMMAND ----------

# MAGIC %fs ls /mnt/bronze/fire_weather_forecast
