'''
------------------------------------------------------------------------------------------
Script: Product Summary ETL Pipeline

Purpose:
- Extract product-level transactional data from source tables in 'inventory_db'
- Transform data to compute aggregated metrics such as quantities, revenue, and profitability
- Load the processed data into the 'product_summary' table for analytical use

Scope:
- Implements full ETL pipeline (Extraction, Transformation, Ingestion)
- Combines data from purchases, sales, and product master tables
- Produces a curated dataset for product performance and margin analysis

Transformation Logic:
- Aggregates purchase and sales metrics at product level
- Cleans and standardizes data (null handling, type casting, string trimming)
- Computes derived KPIs:
  - Gross Profit
  - Gross Profit Margin (%)

Dependencies: sqlalchemy, pymysql, python-dotenv
  
Notes:
- Represents transformation layer of the data pipeline
- Idempotent execution due to table truncation before load
- Requires environment variables for secure database connectivity
--------------------------------------------------------------------------------------------
 '''

# import libraries
import pandas as pd
from sqlalchemy import create_engine,text
from sqlalchemy.engine import URL, Engine
from sqlalchemy.exc import SQLAlchemyError
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

# load env file and import credentials
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PASSWORD = os.getenv("DB_PASSWORD")
if not all([DB_USER, DB_HOST, DB_PASSWORD]):
    raise EnvironmentError("Missing required environment variables.")

# defining project root and log directory
BASE_DIR = Path(__file__).resolve()
while BASE_DIR.name != 'retail-inventory-analytics':
    if BASE_DIR.parent == BASE_DIR:
        raise Exception("retail-inventory-analytics directory not found in the path.")
    BASE_DIR = BASE_DIR.parent

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok = True)

# basic config for log file
logging.basicConfig(
    filename = LOG_DIR /"logs_product_summary_etl.log",
    filemode = "w",
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s"
)

# ======================== Extraction Function ========================
# ---------------------------------------------------------------------
''' The function expects the database engine as parameter.
    And returns a dataframe created by running SQL query.'''
 
def data_extraction(conn_engine):
    logging.info("Extraction Begin ...")

    if not isinstance(conn_engine, Engine):
        raise TypeError("Extraction Failed : Invalid Database Connection Engine")
    
    start = time.time()

    # the query uses CTEs,JOINS,Aggregation to generate summary data
    query = ''' 
            with 
                PurchaseInfo as (
                select
                    ProductId,
                    sum(Quantity) as TotalQuantityPurchased,
                    sum(Dollars) as TotalPurchaseDollars
                from purchases
                where PurchasePrice > 0
                group by ProductId),
                        
                SalesInfo as (
                select
                    ProductId,
                    round(sum(SalesQuantity*SalesPrice)/sum(SalesQuantity),2) as SalesPrice,
                    sum(SalesQuantity) as TotalQuantitySold,
                    sum(SalesDollars) as TotalSalesDollars
                from sales
                where SalesPrice > 0
                group by ProductId)
                
            select
                pp.ProductId,
                pp.Description,
                pp.VendorNumber,
                pp.VendorName,
                pp.Volume as Volume_ml,
                pp.Price as ActualPrice,
                pp.PurchasePrice,
                pi.TotalQuantityPurchased,
                pi.TotalPurchaseDollars,
                si.SalesPrice,
                si.TotalQuantitySold,
                si.TotalSalesDollars
            from purchase_prices pp
            left join PurchaseInfo pi
                on pp.ProductId = pi.ProductId
            left join SalesInfo si
                on pp.ProductId = si.ProductId
            '''
    # store summary result as a dataframe
    with conn_engine.connect() as conn:
        df= pd.read_sql(text(query),conn)

    end=time.time()
    if df.empty:
        raise ValueError("Extraction failed: no data received from source query.")
    
    time_taken = round(end-start,2)
    logging.info(f"Extraction End.Total Records:{len(df)}.Time taken:{time_taken} seconds.")
    return df    # return created dataframe
    
# ======================== Transformation Function ========================
# -------------------------------------------------------------------------

''' The function expects a dataframe as parameter.
    The updated dataframe is then returned by the function .'''
 
def data_transformation(df):
    logging.info("Transformation Begin ...")

    # check if dataframe is not empty
    if df.empty:
        raise ValueError("Transformation failed: input dataframe is empty")

    start = time.time()

    # drop records where item quantity sold or purchased is unknown
    df = df.dropna(subset=['TotalQuantityPurchased','TotalQuantitySold']).copy()

    # handle missing values in numerical fields
    num_cols = df.select_dtypes(include='number').drop(labels=['VendorNumber','ProductId'], axis=1).columns
    df.loc[:, num_cols] = df[num_cols].fillna(0)

    # convert Volume, Quantities Sold and Purchased fields to integer datatype
    df = df.astype({'Volume_ml':int,'TotalQuantityPurchased':int,'TotalQuantitySold':int})

    # remove unwanted space from categorical columns
    cat_cols = df.select_dtypes(include=["object", "string"]).columns
    df.loc[:, cat_cols]  = df[cat_cols].apply(lambda col: col.str.strip())

    # Create new calculated columns for deeper analysis
    # Gross Profit and Gross Profit Margin(in %) 
    df['GrossProfit'] = df['TotalSalesDollars'] - df['PurchasePrice']*df['TotalQuantitySold']

    df['GrossProfitMargin'] = (df['GrossProfit'] * 100 /
                               df['TotalSalesDollars'].mask(df['TotalSalesDollars'] == 0)).fillna(0)
    
    # round off values in fields of float datatype
    df = df.round(2)

    end= time.time()
    time_taken = round(end-start,2)
    logging.info(f"Transformation End. Resultant records:{len(df)}.Time taken: {time_taken} seconds.")
    return df  # return transformed dataframe

# ======================== Ingestion Function ========================
# --------------------------------------------------------------------

''' The function expects parameters :
        df         : Dataframe whose data will be loaded into the target table.   
        table_name : Name of target table which will be created and data will be ingested into it.
        conn_engine: Database engine establishing connection to the database.
    The function starts a transaction and inserts data. In case of an error, entire
    operation rolls back.
'''
def data_ingestion(df ,table_name : str , conn_engine):
    logging.info("Ingestion Begin ...")
    
    if not isinstance(conn_engine, Engine):
        raise TypeError("Ingestion Failed : Invalid Database Connection Engine")
    if df.empty:
        raise ValueError("Ingestion failed: input dataframe is empty")
    if not table_name or not table_name.strip():
        raise ValueError("Ingestion failed: input table name is invalid")
    
    start = time.time()
    # start a transaction and perform operation
    with conn_engine.begin() as conn:
        conn.execute(text(f"truncate table {table_name};"))
        df.to_sql(table_name, conn, if_exists ='append', index =False)
        row_count = conn.execute(text(f"select count(*) from {table_name};")).scalar()

    if row_count == 0:
        raise ValueError("Ingestion failed: target table is empty after load")
    
    end = time.time()
    time_taken = round(end-start,2)
    logging.info(f"Ingestion End.Total Records :{row_count}.Time taken: {time_taken} seconds.")

# =========================== ETL Process ===========================
# -------------------------------------------------------------------

if __name__ == '__main__' :
    final_start = time.time()

    # Create database engine connection to "inventory_db" database
    conn_eng = None
    try:
        database_url = URL.create(
            drivername = "mysql+pymysql",
            username = DB_USER,
            host = DB_HOST,
            password = DB_PASSWORD,
            database = "inventory_db"
        )
        conn_eng = create_engine(database_url)

        with conn_eng.connect() as conn:
            conn.execute(text("select 1;"))
        
        logging.info("<<< Database Connection Established >>>")

        logging.info("ETL Process Begin :")

        # extract summary data and store as dataframe (call extraction function)
        summary_df = data_extraction(conn_engine = conn_eng)

        # update summary dataframe after transformation (call transformation function)
        summary_df = data_transformation(summary_df)

        # load summary data as a table in the database (call ingestion function)
        data_ingestion(
            df = summary_df,
            table_name = "product_summary",
            conn_engine = conn_eng)
        
    except (ValueError,TypeError) as e:
        logging.error(f"[ETL Fail] {e}")
        raise
        
    except SQLAlchemyError as e:
        logging.exception("Database Error occured during ETL ")
        raise

    except Exception as e:
        logging.exception("Unexpected Error occured during ETL ")
        raise

    finally:
        final_end = time.time()
        final_time = round(final_end - final_start,2)
        logging.info(f"ETL Process End.Total time taken: {final_time} seconds")

        if conn_eng :
            conn_eng.dispose()
            logging.info("xxx  Database Connection closed  xxx")

# ------------------------------------------------------------------------------