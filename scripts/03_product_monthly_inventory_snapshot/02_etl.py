'''
--------------------------------------------------------------------------------------------------
Script: Product Monthly Inventory ETL Pipeline

Purpose:
- Extract product level inventory movement data from transactional tables in 'inventory_db'
- Compute month wise inventory metrics including opening stock, purchases, sales, and closing stock
- Load the processed data into the 'product_monthly_inventory' table for time-series analysis

Scope:
- Implements ETL pipeline (Extraction, Ingestion) for monthly inventory aggregation
- Generates complete product month combinations to ensure continuous time-series coverage
- Uses SQL-based transformations (CTEs, window functions, cumulative calculations)

Transformation Logic:
- Generates monthly calendar using recursive CTE
- Aggregates purchase and sales quantities at product-month level
- Computes:
  - Opening Stock (based on prior cumulative movement)
  - Purchase Quantity and Sales Quantity
  - Closing Stock (running inventory balance)
- Handles missing values using COALESCE for accurate calculations

Dependencies: sqlalchemy, pymysql, python-dotenv

Notes:
- Represents analytical (time-series) layer of the data pipeline
- Idempotent execution due to table truncation before load
- Requires environment variables for secure database connectivity
---------------------------------------------------------------------------------------------------
'''

# import libraries
import pandas as pd
from sqlalchemy import create_engine,text
from sqlalchemy.engine import URL,Engine
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
    filename = LOG_DIR /"logs_product_monthly_inventory_etl.log",
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
                with recursive fomonth as (
                        select date('2024-01-01') as month_startdate
                        union all
                        select date_add(month_startdate,interval 1 month)
                        from fomonth
                        where month_startdate < '2024-12-01'),
                        
                    product_month_table as (
                        select p.ProductId, 
                            m.month_startdate
                        from (select distinct ProductId from purchase_prices) p
                        cross join fomonth m),
                        
                    product_monthly_purchase as (
                        select ProductId,
                            date_format(ReceivingDate,'%Y-%m-01') as month,
                            sum(Quantity) as PurchaseQuantity
                        from purchases
                        group by ProductId, month
                        ),
                        
                    product_monthly_sales as (
                        select ProductId,
                            date_format(SalesDate,'%Y-%m-01') as month,
                            sum(SalesQuantity) as SalesQuantity
                        from sales
                        group by ProductId, month
                        ),
                        
                    product_openingstock as (
                        select ProductId, 
                            sum(onHand) as Initial_OpeningStock
                        from begin_inventory
                        group by ProductId),
                    
                    base_table as (
                        select pm.ProductId,
                            pm.month_startdate,
                            coalesce(p.PurchaseQuantity,0) as PurchaseQuantity,
                            coalesce(s.SalesQuantity,0) as SalesQuantity
                        from product_month_table pm
                        left join product_monthly_purchase p
                            on pm.ProductId = p.ProductId and pm.month_startdate = p.month 
                        left join product_monthly_sales s
                            on pm.ProductId = s.ProductId and pm.month_startdate = s.month),

                    inventory_calc as (
                        select b.ProductId,
                            b.month_startdate,
                            os.Initial_OpeningStock,
                            b.PurchaseQuantity,
                            b.SalesQuantity,
                            sum(b.PurchaseQuantity - b.SalesQuantity) over(
                                    partition by b.ProductId order by b.month_startdate
                                    ) as cumulative_movement
                        from base_table b
                        left join product_openingstock os
                        on b.ProductId = os.ProductId
                )
                select ProductId,
                    month_startdate,
                    Initial_OpeningStock + coalesce(lag(cumulative_movement) over(
                                        partition by ProductId order by month_startdate), 0) AS OpeningStock,
                    PurchaseQuantity,
                    SalesQuantity,
                    Initial_OpeningStock + cumulative_movement as ClosingStock
                from inventory_calc
                order by ProductId, month_startdate;
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

        # load summary data as a table in the database (call ingestion function)
        data_ingestion(
            df = summary_df,
            table_name = "product_monthly_inventory",
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