# Databricks notebook source
# MAGIC %md
# MAGIC # Testing out reading different filetypes
# MAGIC ## install notebook scoped libraries

# COMMAND ----------

# MAGIC %pip install /dbfs/databricks/libraries/pyrasterframes-0.10.1.dev0+dbr7.3-py3-none-any.whl

# COMMAND ----------

# MAGIC %pip install pyshp

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

weather_station.write.saveAsTable('weather_station', format='delta', mode='overwrite')

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

# setting up path in case we need to process in parallel 
rdps_path = f"/dbfs{bronze_path}/rdps_pr/"
path = Path(rdps_path)
print(path)

# COMMAND ----------

# MAGIC %fs ls /mnt/bronze/rdps_pr

# COMMAND ----------

rf = spark.read.raster("/dbfs/mnt/bronze/rdps_pr/RDPS.ETA_PR-2021121500.tiff")
rf.printSchema()

# COMMAND ----------

crs = rf.select(rf_crs("proj_raster")).first()[0]
print(crs)

# COMMAND ----------

rf.select(
  rf_extent("proj_raster").alias("extent"),
  rf_tile("proj_raster").alias("tile")
)

# COMMAND ----------

tile = rf.select(rf_tile("proj_raster")).first()[0]
tile.show()

# COMMAND ----------

# MAGIC %md 
# MAGIC ### Create a catalog

# COMMAND ----------

from pyspark.sql import Row
import os

raster_list = [rdps_path + tiff for tiff in os.listdir(rdps_path)]

row = Row('shapefile_path') 
raster_rdd = sc.parallelize(raster_list)
catalog_rdps = (
  raster_rdd.map(row)
    .toDF()
)

display(catalog_rdps)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Multiple singleband rasters

# COMMAND ----------



# COMMAND ----------

# DBTITLE 1,Question: Can we pull these raster images from an external source?
# from pyspark import SparkFiles
# from pyspark.sql import functions as F

# spark.sparkContext.addFile("https://modis-pds.s3.amazonaws.com/MCD43A4.006/2018-07-04_scenes.txt")

# scene_list = spark.read \
#     .format("csv") \
#     .option("header", "true") \
#     .load(SparkFiles.get("2018-07-04_scenes.txt"))
# scene_list

# COMMAND ----------



# COMMAND ----------

# MAGIC %md
# MAGIC ## Fire Weather Forecast (Shapefile)

# COMMAND ----------

# MAGIC %fs ls /mnt/bronze/fire_weather_forecast

# COMMAND ----------

import os
from os.path import exists
from pathlib import Path

# COMMAND ----------

# setting up path in case we need to process in parallel 
fwf_path = f"/dbfs{bronze_path}/fire_weather_forecast/"
path = Path(fwf_path)
print(path)

# COMMAND ----------

num_cores = sc.defaultParallelism
print(f'We currently have {num_cores} worker cores available to us.')

# COMMAND ----------

shp_files = os.listdir(path)
for file in shp_files:
  print(file)

# COMMAND ----------

shapefile_list = [fwf_path + shapefile for shapefile in os.listdir(fwf_path)]
print(shapefile_list)

# COMMAND ----------

print(fwf_path)

# COMMAND ----------

from pyspark.sql import Row

# This might not be needed but this allows us to search through a directory structure and ingest many shapefiles
# suggested directory structure bronze/shapefiles/WF_WEATHER_FCST_ZONE_S3_GCSWGS84

# shapefile_list = [fwf_path + shapefile for shapefile in os.listdir(fwf_path)]

shapefile_list = [fwf_path + 'WF_WEATHER_FCST_ZONE_S3_GCSWGS84']

row = Row('shapefile_path') 
shapefile_rdd = sc.parallelize(shapefile_list)
shapefile_df = (
  shapefile_rdd.map(row)
    .toDF()
)

display(shapefile_df)

# COMMAND ----------

import shapefile
from pyspark.sql.types import MapType, ArrayType, StringType

def shapefile_reader(shapefile_path):
  with shapefile.Reader(shapefile_path) as shp:
      shape_records = []

      # Iterate through each shape record
      for shape in shp.shapeRecords():
        shape_record = shape.record.as_dict() # Read record
        geojson = {'geojson':shape.shape.__geo_interface__.__str__()} # Read shapefile GeoJSON
        shape_records.append({**shape_record, **geojson}) # Concatenate and append
        
  return(shape_records)

# Register udf
shapefile_reader_udf = udf(shapefile_reader, ArrayType(MapType(StringType(), StringType())))

# COMMAND ----------

# MAGIC %md
# MAGIC apply the udf. See [user-defined functions in python](https://docs.databricks.com/spark/latest/spark-sql/udf-python.html#user-defined-functions---python)

# COMMAND ----------

read_shapefile_result = shapefile_df.withColumn('shapefile_data', shapefile_reader_udf('shapefile_path'))

# COMMAND ----------

read_shapefile_result.show()

# COMMAND ----------

# MAGIC %md Since the output of the `udf` is an array, we explode the column to return a row for each shape record (and corresponding shape) across all the shapefiles.

# COMMAND ----------

from pyspark.sql.functions import explode

exploded = (read_shapefile_result
            .select('shapefile_data')
            .withColumn('exploded', explode('shapefile_data'))
            .drop('shapefile_data')
           )
display(exploded)

print(f'We had {shapefile_df.count()} shapefiles with a total of {exploded.count()} shapes.')

# COMMAND ----------

# MAGIC %md Assuming the schemas for the records are consistent, we can flatten it out into a more useful format

# COMMAND ----------

from pyspark.sql.functions import col

flatten_keys = list(exploded.limit(1).collect()[0][0].keys())

expanded = [col("exploded").getItem(k).alias(k) for k in flatten_keys]
flattened = exploded.select(*expanded)

display(flattened)

# COMMAND ----------

flattened.printSchema()

# COMMAND ----------

# DBTITLE 1,Write data out to delta
flattened.write.saveAsTable('shapefiles', format='delta', mode='overwrite')

# COMMAND ----------

# MAGIC %sql
# MAGIC select
# MAGIC   WFZ_ID,
# MAGIC   Shape_Area,
# MAGIC   NAME
# MAGIC from
# MAGIC   shapefiles
# MAGIC order by Shape_Area DESC

# COMMAND ----------


