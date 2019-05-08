#----------------------------
## Introduction 
#----------------------------

# This course aims to give you hands on experience in working with the DataFrame 
# API in PySpark. We will not cover all functionality but instead focus on getting 
# up and running and performing a few common operations on an example dataset. 
#
### Format 
#
#   * Walkthrough typical data analysis
#   * Several short exercises to build familiarity, 
#   * Some more in-depth exercises to explore after the course.
#   * You will have access to the training environment for a short time following
#     the course.
# 
### Prerequisites:
#
#  * Basic Python, 
#  * SQL and `pandas` optional but beneficial

### CDSW Environment

# * Work is performed in specifically created Sessions (linux container), and attached to 
#  the project. 
# * Different languages possible (Python, R Scala)
# * Basic file browser, basic editor + REPL
# * Run code in editor with Ctr+Enter for current line or 'Run all lines' button
#
# Additional Features:
# * Comments are rendered as Markdown 
# * Terminal Access provided to the linux container

### Setup

# 'Fork' this project and select your username as the destination, this gives you your 
# own copy of this matieral to work with for this session. Environment variables have also
# been setup for you. 

# Note, some additional setup is required when working in DAP, specifically:
#  * Authentication to the cluster (Account settings --> Hadoop authentication, enter windows credentials)
#
#  * Setting Environemnt variable to tell Pyspark to use Python 3:
#  * `PYSPARK_PYTHON` = `/usr/local/bin/python3`
#  
#  * Setting up the link to Artifactory to install Python packages:
# * `PIP_INDEX_URL` = `http://<USERNAME>:<PASSWORD>@art-p-01/artifactory/api/pypi/yr-python/simple` 
# * `PIP_TRUSTED_HOST` = `art-p-01`
# * Where `<USERNAME>` is your windows username and `<PASSWORD>` is your hashed password from artifactory
#    (see instructions, artifactory section; https://share.sp.ons.statistics.gov.uk/sites/odts/wiki/Wiki/Components%20Introduction.aspx)


### Import all necessary packages to work with Spark

from pyspark.sql import SparkSession
import pyspark.sql.functions as f

# Functions are kept in 2 places in PySpark:
# * The `pyspark.sql.functions` module
# * Attached to the `DataFrame` or `Column` object itself

# To find out the functions available in the sql module
dir(f)

### Finding Help

# To get more help with a module/function
help(f.to_date)

# Though even better is to have the html docs at hand
# https://spark.apache.org/docs/latest/api/python/index.html

#----------------------------
## Configure the Spark Session
#----------------------------

# For this Training setup: 
#  *  max executor cores = 2
#  *  max executor memory = 1500m (this included overheads)

spark = (
    SparkSession.builder.appName("my-spark-app")
    .config("spark.executor.memory", "1500m")
    .config("spark.executor.cores", 2)
    .config("spark.dynamicAllocation.enabled", 'true')
    .config('spark.dynamicAllocation.maxExecutors', 4)
    .config('spark.shuffle.service.enabled','true')
    .enableHiveSupport()
    .getOrCreate()
)

# Handy option for better output display in pandas dfs
import pandas as pd
pd.set_option("display.html.table_schema", True)

#----------------------------
## Load the Data
#----------------------------

# Use CSV in this session, though most big datasets will be read from HDFS (More on that later)

### From HDFS

# To find data if its on HDFS as a HIVE table
spark.sql("show databases").show(truncate=False)

# To find what tables are in the database
spark.sql("use training")
spark.sql("show tables").show(truncate=False)

# Reading Data from SQL
sdf = spark.sql("SELECT * FROM department_budget")
sdf

# Note that the table is not yet displayed
# Spark is built on the concept of transformations and actions.
#   * **Transformations** are lazily evaluated expressions. This form the set of 
#     instructions that will be sent to the cluster.  
#   * **Actions** trigger the computation to be performed on the cluster and the 
#     results accumulated locally in this session.
#
# Multiple transformations can be combined, and only when an action is triggered 
# are these executed on the cluster, after which the results are returned. 

sdf.show(10)

# The default returned results can look pretty ugly when you get a lot of columns, 
# so best way to visualise is to explore them is to convert to a pandas DataFrame,
# which are then displayed as HTML tables
df = sdf.toPandas()
df

### Reading in Data From a CSV

#### Data set: Animal rescue incidents by the London Fire Brigade.

rescue = spark.read.csv(
    "/tmp/training/animal-rescue.csv", 
    header=True, inferSchema=True, 
)

# To just get the column names and data types
rescue.printSchema()

# The `.show()` function is an action that displays a DataFrame and has defaults of 
# `.show(n=20, truncate=True)`.
rescue.show(10, truncate=False)

# It can get real messy to display everything this way with wide data, recomendations are:
# 1.  Subset to fewer columns
# 2.  convert to pandas df
# 3.  copy to text file

# Option 1 
rescue.select('DateTimeOfCall', 'FinalDescription', 'AnimalGroupParent').show(truncate=False)

# Option 2
# Warning converting to pandas will bring back all the data, so first subset the rows 
# with limit
rescue_df = rescue.limit(10).toPandas()
rescue_df

# Option 3
# Use .show(truncate=False) and highlight the output in the right hand side, then copy 
# and paste to a new file. 

#----------------------------
## Data Preprocessing
#----------------------------

# First, there are a lot of columns related to precise geographic position
# which we will not use in this analysis, so lets drop them for now.
rescue = rescue.drop(
    'WardCode', 
    'BoroughCode', 
    'Easting_m', 
    'Northing_m', 
    'Easting_rounded', 
    'Northing_rounded'
)
rescue.printSchema()

# Rename column to a more descriptive name
rescue = rescue.withColumnRenamed("PumpCount", "EngineCount")
rescue = rescue.withColumnRenamed("FinalDescription", "Description")
rescue = rescue.withColumnRenamed("HourlyNotionalCost(£)", "HourlyCost")
rescue = rescue.withColumnRenamed("IncidentNotionalCost(£)", "TotalCost")
# Fix a typo 
rescue = rescue.withColumnRenamed("OriginofCall", "OriginOfCall")

rescue.printSchema()

## Exercise 1 ##########################################################################

#> Rename PumpHoursTotal --> JobHours
#>
#> Rename AnimalGroupParent --> AnimalGroup


########################################################################################

### Convert Dates from String to Date format

# Here we make use of the additional functions in sql module we imported earlier,
# and operate on a single column using withColumn to select it.
rescue = rescue.withColumn(
    "DateTimeOfCall", f.to_date(rescue.DateTimeOfCall, "dd/MM/yyyy")
)
rescue.printSchema()
rescue.limit(10).toPandas()

### Filter data to just last 7 years

recent_rescue = rescue.filter(rescue.CalYear > 2012)
# Or equivilantly
recent_rescue = rescue.filter('CalYear > 2012')

recent_rescue.limit(10).toPandas()


## Exercise 2 ############################################################################

#> Filter the recent data to find all the those with AnimalGroup equal to 'Fox'



##########################################################################################


#----------------------------
## Data Exploration 
#----------------------------

### Investigate `IncidentNumber`

# Find the number of Rows and Columns
n_rows = rescue.count()
n_columns = len(rescue.columns)

# We have an IncidentNumber column, lets check that this is unique.
n_unique = rescue.select("IncidentNumber").distinct().count()
n_rows == n_unique

### Exploring `AnimalGroups`

# Next lets explore the number of different animal groups
n_groups = rescue.select("AnimalGroup").distinct().count()
n_groups

# What are they?
animal_groups = rescue.select("AnimalGroup").distinct()
animal_groups.toPandas()


### Adding Columns and Sorting

# `JobHours` gives the total number of hours for engines attending the incident, 
# e.g. if 2 engines attended for an hour JobHours = 2
# 
# So to get an idea of the duration of the incident we have to divide JobHours 
# by the number of engines in attendance. 
#
# Lets add another column that calculates this

# withColumn can be used to either create a new column, or overwrite an existing one.
rescue = rescue.withColumn(
    "IncidentDuration", 
    rescue.JobHours / rescue.EngineCount
)

rescue.printSchema()

# Lets subset the columns to just show the incident number, duration, total cost and description
result = rescue.select("IncidentNumber", "TotalCost", "IncidentDuration", "Description")

result.show(truncate=False)

# Lets investigate the highest total cost incidents
result = (
    rescue.select("IncidentNumber", "TotalCost", "IncidentDuration", "Description")
    .sort("TotalCost", ascending=False)
)

result.limit(10).toPandas()

# Seems that horses make up a lot of the more expensive calls, makes sense.


## Exercise 3 ################################################################################

#> Sort the incidents in terms of there duration, look at the top 10 and the bottom 10.

#> Do you notice anything strange?


##############################################################################################

# So it looks like we may have a lot of missing values to account for (which is why there are 
# a lot of blanks).

## Handeling Missing values

# Lets count the number of missing values in these columns. Columns have a `isNull` and 
# `isNotNull` function, which can be used with `.filter()` 

rescue.filter(rescue.TotalCost.isNull()).count()

rescue.filter(rescue.IncidentDuration.isNull()).count()

# Looks like this effects just 38 rows, for now lets row these from the dataset. We 
# could combine the two above operations. Or use the `.na.drop()` function on DataFrames
rescue = rescue.na.drop(subset=["TotalCost", "IncidentDuration"])

# Now lets rerun our sorting from above.
bottom_10 = (
    rescue.select("IncidentNumber", "TotalCost", "IncidentDuration", "Description")
    .sort("IncidentDuration", ascending=True)
    .limit(10)
)
bottom_10.toPandas()

# Much better.


#### Side note on sorting and Spark's API

# Confusingly, there are often several ways to interact with the Spark API to get the 
# same result. Part of this is by design to allow it to support SQL like phrasing of 
# commands, and some is due to the evolution of the API.
#
# Sorting is one place you may come across this. All the below do the same thing!
# 
# ```python
#   import pyspark.sql.functions as f
#   df.sort(f.desc("age"))
#   df.sort(df.age.desc())
#   df.sort("age", ascending=False)
#   df.orderBy(df.age.desc())
# ```

# And if you wanted to sort by multiple columns, you have a few options too.
# 
# ```python
#   import pyspark.sql.functions as f
#   df.sort(["age", "name"], ascending=False)
#   df.orderBy(f.desc("age"), "name")
#   df.orderBy(["age", "name"], ascending=[0, 1])
# ```
#
# Advice is to be consistent in using one approach. Here I've used the syntax 
# thats most similar to pandas with `df.sort("age", ascending=False)`

## Adding Indicator Variables/Flags

# Lets create some extra columns to act as flags in the data to indicate rows of interest
# for downstream analysis. Typically these are set based on a particular grouping or
# calculation result we want to remember.

# For this example lets look at all the incidents that involved snakes in someones
# home (Dwelling).
rescue = rescue.withColumn(
    "SnakeFlag", f.when(rescue.AnimalGroup == "Snake", 1).otherwise(0)
)

# Note that we can filter with multiple conditions using the pipe `|` to mean OR and 
# `&` to mean AND. Each condition must be surrounded with parenthesis. 
recent_snakes = rescue.filter((rescue.CalYear > 2015) & (rescue.SnakeFlag == 1))
recent_snakes.toPandas()


## Exercise 4 ####################################################################################

#> Add an additional flag to indicate when PropertyCategory is 'Dwelling'.

#> Subset the data to rows when both the 'snake' and 'property' flag is 1

##################################################################################################

#----------------------
## Analysing By Group 
#----------------------

# Lets look at this more closely and find the average cost by AnimalGroup
cost_by_animal = rescue.groupBy("AnimalGroup").agg(f.mean("TotalCost"))
cost_by_animal.printSchema()

# Lets sort by average cost and display the highest
cost_by_animal = cost_by_animal.sort("avg(TotalCost)", ascending=False).limit(10).toPandas()

# Notice anything out the ordinary?

# Lets compare the number of Goats vs Horses. We can filter with multiple conditions
# using the pipe `|` to mean OR and `&` to mean AND.
goat_vs_horse = rescue.filter(
    (rescue.AnimalGroup == "Horse") | (rescue.AnimalGroup == "Goat")
)
goat_vs_horse.limit(10).toPandas()

# Count the number of each animal type
goat_vs_horse.groupBy("AnimalGroup").agg(f.count("AnimalGroup")).show()

# Lets see what that incident was.
result = (
    rescue.filter(rescue.AnimalGroup == "Goat")
    .select('AnimalGroup', 'JobHours', 'Description')
    .limit(10).toPandas()
)

# Just one expensive goat it seems!

### Combining Multiple Operations with Method Chaining

# Note, the above was a fair bit of work involving multiple stages. Once we 
# are more clear with what we want, several of these steps can be combined by
# chaining them together. Code written in this way gets long fast, and so its 
# encouraged to lay it out verticaly with indentation, and use parentheses to
# get python to evaluate expressions over multiple lines. 

avg_cost_by_animal = (
    rescue.filter(
        (rescue.AnimalGroup == "Horse") | (rescue.AnimalGroup == "Goat")
    )
    .groupBy("AnimalGroup")
    .agg(
        f.avg('TotalCost'))
    .sort("avg(TotalCost)", ascending=False)
    .toPandas()
)
avg_cost_by_animal

## Exercise 5 ################################################################################

#> Get total counts of incidents for each different animal types


#> Sort the results in descending order and show the top 10


##############################################################################################

### A Few Tips and Tricks

# I've rewritten the above method chaining example using a few additional functions to give it more 
# flexibly, like `.isin()` and making use of mutliple functions to`.agg()`, 
#
# Note also that the `alias()` function is a way of specifying the name of the column
# in the output 

avg_cost_by_animal = (
    rescue.filter(
        rescue.AnimalGroup.isin(
            "Horse", 
            "Goat", 
            "Cat", 
            "Bird"
        ))
    .groupBy("AnimalGroup")
    .agg(
        f.min('TotalCost').alias('Min'), 
        f.avg('TotalCost').alias('Mean'), 
        f.max('TotalCost').alias('Max'), 
        f.count('TotalCost').alias('Count'))
    .sort("Mean", ascending=False)
    .toPandas()
)
avg_cost_by_animal


#------------------------
## Joining Data
#------------------------

# Lets load in another data source to indicate population based on postcode, and join that 
# onto the rescue data

filepath = "/tmp/training/population_by_postcode.csv"
population = spark.read.csv(filepath, header=True, inferSchema=True)
population.printSchema()
population.show()

# We have this for each postcode, so lets aggregate before joining
outward_code_pop = (
    population.select('OutwardCode', 'Total')
    .groupBy('OutwardCode')
    .agg(f.sum('Total').alias('Population'))
)
outward_code_pop.show()

# Now lets join this based on the Postcode Outward code

# As these columns names are slightly different, we can express this mapping in the
# on argument.
rescue_with_pop = (
    rescue.join(
        outward_code_pop,
        on=rescue.PostcodeDistrict == outward_code_pop.OutwardCode,
        how="left")
    .drop("OutwardCode")
)

rescue_with_pop.limit(10).toPandas()

#---------------------------
## Using SQL
#---------------------------

# You can also swap between pyspark and sql during your workflow

# As we read this data from CSV (not from a Hive Table), we need to first register a
# temporary table to use the SQL interface. If you have read in data from an existing SQL 
# table, you don't need this step
rescue.registerTempTable('rescue')

# You can then do SQL queries 
result = spark.sql(
    """SELECT AnimalGroup, count(AnimalGroup) FROM rescue
            GROUP BY AnimalGroup
            ORDER BY count(AnimalGroup) DESC"""
)
result.limit(10).toPandas()

## Exercise 6 ###############################################################################

# >Using SQL, find the top 10 most expensive call outs aggregated by the total sumed cost for 
# >each AnimalGroup. 



############################################################################################

#------------------------------
## Writing Data
#------------------------------

## To HDFS
path = '/user/username/rescue_with_pop.parquet'
rescue_with_pop.write.parquet(path)

# Note that if the file exists, it will not let you overwright it. You must first delete
# it with the hdfs tool. This can be run from the console with 
!hdfs dfs -rm -r /user/username/rescue_with_pop.parquet

# Also note that each user and workspace will have its own home directory which you can,
# save work to.
# ````python
# username='your-username-on-hue'
# rescue_with_pop.write.parquet(f'/user/{username}/rescue_with_pop.parquet')
# ````

# Benefits of parquet is that type schema are captured
# Its also a column format which makes loading in subsets of columns a lot faster for 
# large datasets.

# However it is not designed to be updated in place (imutable), so may have to delete and 
# recreate files, which requires using the terminal commands. It is also harder to view 
# the data in HUE, as it first needs to be loaded into a table (beyond the scope of this
# session).

# There are also methods for writing CSV and JSON formats. 

## To a SQL Table (HIVE)

rescue.registerTempTable('rescue_with_pop')
spark.sql('CREATE TABLE training.my_rescue_table AS SELECT * FROM rescue_with_pop')

# Delete table
spark.sql('DROP TABLE IF EXISTS training.my_rescue_table')


## Final Exercise Questions

# 1. How much do cats cost the London Fire Brigade each year on average? 
# 2. What percentage of their total cost (across all years) is this?
# 3. Extend the above to work out the percentage cost for each animal type.
# 4. Which Postcode districts reported the most and least incidents?
# 5. When normalised by population count, which Postcode districts report the most and least incidents (incidents per person)?
# 6. Create outputs for the above questions and save them back to hdfs as a csv file
# in your users home directory. 

#-----------------------
## Tips and Tricks
#-----------------------

### Editor

#* double click = selct word; tripple click = select whole line

#* Tab completion

#* Run larger sections with - Shift + PgUp / PgDn then Ctr+Enter

#* Clear the Console output with Ctr+L

### IPython

#* Show defined variables: who / whos

#* Clear all variables: reset

#* Directory navigation and file operations: pwd / cd / ls / mv / cp

#-----------------------
## Further Resource
#-----------------------
#
# * Pluralsight Courses
#
# * PySpark Documentation
#
# * StackOverflow
#
# * Text Books
#    *  Spark the Definitive Guide: https://www.amazon.co.uk/Spark-Definitive-Guide-Bill-Chambers/dp/1491912219
#
# * Data Explorers Slack Channel