# Databricks notebook source
# MAGIC %md 
# MAGIC # Set up configuration
# MAGIC ## Libraries

# COMMAND ----------

#%pip install /dbfs/databricks/libraries/pyrasterframes-0.10.1.dev0+dbr7.3-py3-none-any.whl

# COMMAND ----------

# MAGIC %md
# MAGIC ## Path and database configuration

# COMMAND ----------

dbutils.widgets.removeAll()

# COMMAND ----------

project = "wwxf"
dbutils.widgets.text("projectid", project, "project") # name, value, label

# COMMAND ----------

from pyspark.sql.functions import rand, input_file_name, from_json, col
from pyspark.sql.types import *

# COMMAND ----------

# import mlflow
# import mlflow.spark
# from mlflow.utils.file_utils import TempDir

from time import sleep
import re
import seaborn as sn
import pandas as pd
import matplotlib.pyplot as plt

# COMMAND ----------

def clean_string(a: str) -> str:
  return re.sub('[^A-Za-z0-9]+', '', a).lower()

# COMMAND ----------

user = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().get("user").get()
username = clean_string(user.partition('@')[0])

print("Created variables:")
print("user: {}".format(user))
print("username: {}".format(username))

# user settings
user_dbName = re.sub(r'\W+', '_', username) + "_" + project
user_path = f"/Users/{user}/{project}"
dbutils.widgets.text("user_dbName", user_dbName, "user_dbName")
dbutils.widgets.text("user_path", user_path, "user_path")
print(f"user path (user path): {user_path}")
print("dbName (using database): {}".format(user_dbName))
spark.sql("""create database if not exists {} LOCATION '{}/{}/tables' """.format(user_dbName, project, user_path))
spark.sql("""USE {}""".format(user_dbName))

print(f"By default using user database {user_dbName}. Please switch to project database if needed")


# project settings -- temporary
dbName = project
bronze_path = f"/mnt/bronze"
silver_path = f"/mnt/silver"
gold_path = f"/mnt/gold"
project_path = f"/{project}" # just temporary until we decide

dbutils.widgets.text("dbName", dbName, "dbName")
dbutils.widgets.text("project_path", project_path, "project_path")
print(f"project path (project path): {project_path}")

spark.sql("""create database if not exists {} LOCATION '{}/tables' """.format(dbName, project))
# spark.sql("""USE {}""".format(user_dbName))
# print("dbName (using database): {}".format(dbName))

# COMMAND ----------

# dbutils.fs.rm("/wwxf/", True)

# COMMAND ----------

# MAGIC %fs ls /

# COMMAND ----------

dbutils.fs.put(
    "/home/geospatial/sme/init_scripts/dbr7.3_miniconda_gdal_3.1.2_warp_install.sh","""
#!/bin/bash
 
# ::: ASSUMPTIONS :::
# - DBR 7.3 LTS
 
# ::: NATIVES :::
# -- add needed natives (ubuntu 18) --
sudo apt-get update && sudo apt-get install --fix-missing -y build-essential python3-dev python-all-dev pkg-config g++ proj-bin libproj-dev libcairo2-dev libjpeg-dev libgif-dev libopenjp2-7-dev proj-bin libproj-dev sqlite3 libsqlite3-dev libboost-dev libgeos-dev
 
# -- add JPG2000 support with JasPer
sudo add-apt-repository "deb http://security.ubuntu.com/ubuntu xenial-security main"
apt-get install -y libjasper-dev
 
# ::: CONDA :::
# -- install miniconda for python 3.7 --
wget https://repo.anaconda.com/miniconda/Miniconda3-py37_4.10.3-Linux-x86_64.sh
sudo bash Miniconda3-py37_4.10.3-Linux-x86_64.sh -b -u -p /usr/local
 
# -- config conda --
conda update -n base -c defaults -y conda
conda config --set unsatisfiable_hints True
conda --debug update -n base --channel conda-forge --all --yes --quiet
 
# -- install gdal=3.1.2 --
conda install --yes --channel conda-forge gdal=3.1.2
 
# ::: Databricks PIP :::
# - https://github.com/locationtech/rasterframes/blob/develop/pyrasterframes/src/main/python/requirements-condaforge.txt
/databricks/python/bin/pip install gdal==3.1.2
/databricks/python/bin/pip install rasterio[s3] rtree
# - pycairo also 
/databricks/python/bin/pip install --upgrade pip setuptools==57.5.0 wheel
/databricks/python/bin/pip install pkgconfig
/databricks/python/bin/pip install deprecation pycairo pyproj shapely tabulate
 
# -- handle gdal warp --
git clone https://github.com/geotrellis/gdal-warp-bindings.git
mv gdal-warp-bindings/src/Makefile gdal-warp-bindings/src/Makefile.bak
 
# - update makefile
cat > gdal-warp-bindings/src/Makefile << 'EOF'
CFLAGS ?= -Wall -Werror -Og -ggdb3 -D_GNU_SOURCE
CXXFLAGS ?= -std=c++14
LDFLAGS ?= $(shell pkg-config gdal --libs) -l:libstdc++.a -lpthread
# MLJ: Use JDK Path (just hardcoding)
  # JAVA_HOME ?= /usr/lib/jvm/java-11-openjdk-amd64
JDK_HOME ?= /usr/lib/jvm/zulu8
GDALCFLAGS ?= $(shell pkg-config gdal --cflags)
BOOST_ROOT ?= /usr/include
OS ?= linux
SO ?= so
ARCH ?= amd64
HEADERS = bindings.h types.hpp flat_lru_cache.hpp locked_dataset.hpp tokens.hpp errorcodes.hpp
 
 
all: tests libgdalwarp_bindings-$(ARCH).$(SO)
 
com_azavea_gdal_GDALWarp.o: com_azavea_gdal_GDALWarp.c
    $(MAKE) -C main java/com/azavea/gdal/GDALWarp.class
    # MLJ: USING JDK_HOME INSTEAD OF JAVA_HOME (JRE ON DATABRICKS)
    $(CC) $(CFLAGS) $(GDALCFLAGS) -I$(JDK_HOME)/include -I$(JDK_HOME)/include/$(OS) -fPIC $< -c -o $@
 
com_azavea_gdal_GDALWarp.obj: com_azavea_gdal_GDALWarp.c
    $(MAKE) -C main java/com/azavea/gdal/GDALWarp.class
    # MLJ: USING JDK_HOME INSTEAD OF JAVA_HOME (JRE ON DATABRICKS)
    $(CC) $(CFLAGS) $(GDALCFLAGS) -I$(JDK_HOME)/include -I$(JDK_HOME)/include/$(OS) -fPIC $< -c -o $@
 
%.o: %.cpp $(HEADERS)
    $(CXX) $(GDALCFLAGS) $(CFLAGS) $(CXXFLAGS) -I$(BOOST_ROOT) -fPIC $< -c -o $@
 
%.obj: %.cpp $(HEADERS)
    $(CXX) $(GDALCFLAGS) $(CFLAGS) $(CXXFLAGS) -I$(BOOST_ROOT) -fPIC $< -c -o $@
 
libgdalwarp_bindings-$(ARCH).$(SO): com_azavea_gdal_GDALWarp.o bindings.o tokens.o errorcodes.o
    $(CC) $(CFLAGS) $^ $(LDFLAGS) -shared -o $@
 
gdalwarp_bindings-$(ARCH).dll: com_azavea_gdal_GDALWarp.obj bindings.obj tokens.obj errorcodes.obj
    $(CC) $(CFLAGS) $^ $(LDFLAGS) -shared -o $@
 
experiments/data:
    $(MAKE) -C experiments data/c41078a1.tif
 
tests: libgdalwarp_bindings-$(ARCH).$(SO)
    $(MAKE) -C unit_tests tests
    $(MAKE) -C main tests
 
clean:
    rm -f *.o
    $(MAKE) -C experiments clean
    $(MAKE) -C unit_tests clean
    $(MAKE) -C main clean
 
cleaner: clean
    rm -f libgdalwarp_bindings-$(ARCH).$(SO) com_azavea_gdal_GDALWarp.h
    $(MAKE) -C experiments cleaner
    $(MAKE) -C unit_tests cleaner
    $(MAKE) -C main cleaner
 
cleanest: cleaner
    $(MAKE) -C experiments cleanest
    $(MAKE) -C unit_tests cleanest
    $(MAKE) -C main cleanest
EOF
 
# - make
make -j$(nproc) -C gdal-warp-bindings/src cleanest
make -j$(nproc) -C gdal-warp-bindings/src
 
# - copy headers to /usr/local/include
# - e.g. test: ls -als /usr/local/include | grep -e 'bindings.h\|com_azavea_gdal_GDALWarp.h'
sudo cp $PWD/gdal-warp-bindings/src/bindings.h /usr/local/include && sudo cp $PWD/gdal-warp-bindings/src/com_azavea_gdal_GDALWarp.h /usr/local/include
 
# - copy libs to /usr/local/lib
# - have to wait for the .so file to exist
# - e.g. test: ls /usr/local/lib | grep "libgdal"
while [ ! -f $PWD/gdal-warp-bindings/src/libgdalwarp_bindings-amd64.so ]; do sleep 1; done
sudo cp $PWD/gdal-warp-bindings/src/libgdalwarp_bindings-amd64.so /usr/local/lib
""", True)
