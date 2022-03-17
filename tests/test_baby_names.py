# Databricks notebook source
# https://github.com/microsoft/nutter
from runtime.nutterfixture import NutterFixture, tag

# COMMAND ----------

# This code can be generated elsewhere and loaded here with %run
def get_table(year, name="my_data"):
  df = spark.table(f'christopherchalcraft_babynames.babynames_{year}')
  df.createOrReplaceTempView(name)

# COMMAND ----------

class TestFixture(NutterFixture):
  def __init__(self):
    self.table_name = "christopherchalcraft_babynames.babynames_2010"
    self.year = 2010
    NutterFixture.__init__(self)
    
  def gen_data(self):
    get_table(self.year, self.table_name)
  
  def assertion_year(self):
    df = spark.read.table(self.table_name)
    assert(df.select('year').distinct().collect()[0][0] == self.year)
    

# COMMAND ----------

result = TestFixture().execute_tests()
print(result.to_string())
is_job = dbutils.notebook.entry_point.getDbutils().notebook().getContext().currentRunId().isDefined()
if is_job:
  result.exit(dbutils)

# COMMAND ----------


