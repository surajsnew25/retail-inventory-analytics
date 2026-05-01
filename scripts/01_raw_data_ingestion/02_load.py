''' 
---------------------------------------------------------------------------------------
Script: Raw Data Ingestion into Inventory Database

Purpose:
- Load raw CSV datasets into corresponding tables in the 'inventory_db'
- Perform full refresh by truncating tables prior to ingestion
- Use MySQL 'LOAD DATA LOCAL INFILE' for efficient bulk loading

Scope:
- Handles ingestion for inventory, purchases, sales, product and vendor related tables
- Implements reusable ingestion function with dynamic column mapping and date handling
- Ensures minimal transformation 

Dependencies: sqlalchemy, pymysql, python-dotenv

Notes:
- Designed as the ingestion (staging) layer of the ETL pipeline
- Idempotent execution,safe to re run due to table truncation
- Supports NULL handling and date parsing during load
- Requires environment variables for database connectivity
-------------------------------------------------------------------------------------------- 
'''

# import libraries
from sqlalchemy import create_engine,text
from sqlalchemy.engine import URL
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
    filename = LOG_DIR /"logs_raw_data_ingest.log",
    filemode = "w",
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s"
)

# =========================== Data Ingestion Function ===========================
# -------------------------------------------------------------------------------
''' The function expects parameters :
        table_name(str)  = Name of the target table in database
        file_path(Path)  = CSV file path corresponding to the target table
        columns(list)    = Column names in order as defined in the structure of target table
        date_col(list)   = Date column names (if any)
    The function TRUNCATES the table and then LOAD data from CSV file into target table.
'''
def data_ingestion_func(table_name : str , file_path : Path,
                        columns : list[str] , date_col: list[str] = None):
    
    # check if file path is valid and convert to string
    if not file_path.exists():
        raise FileNotFoundError(f'File not found in the path - {file_path}')
    file_path = file_path.as_posix()

    # check if table name is valid
    if table_name not in table_names_list:
        raise ValueError(f"Invalid table name. Not found in the predefined list - {table_names_list}")
    
    logging.info(f"[{table_name}] : Ingestion Start (Truncate and Insert) ...")
    start = time.time()

    # column mapping and set expression variable 
    col_variables_list = [f'@{col}' for col in columns]
    col_variables_str = ','.join(col_variables_list)

    # set expression used in query to handle empty values and date formatting
    set_expr_list = []
    for col in columns:
        if date_col and col in date_col:
            set_expr_list.append(f"{col} = str_to_date(nullif(trim(@{col}),''),'%Y-%m-%d')")
        else:
            set_expr_list.append(f"{col} = nullif(trim(@{col}),'')")
    set_expression = ',\n   '.join(set_expr_list)

    # Query to load data from CSV file into target table (Using LOAD DATA INFILE statement)
    query = f'''
            load data local infile '{file_path}'
            into table {table_name}
            fields terminated by ','
            enclosed by '"'
            lines terminated by '\\n'
            ignore 1 rows
            ({col_variables_str})
            set {set_expression} ;
            '''
    
    # Truncate the table and execute the query to load data
    with conn_eng.begin() as conn:
        conn.execute(text(f"truncate table {table_name};"))
        logging.info(f"[{table_name}] : Table truncated")

        conn.execute(text(query))
        row_count = conn.execute(text(f"select count(*) from {table_name}")).scalar()

    end = time.time()
    if row_count == 0:
        logging.warning(f"[{table_name}] : No records loaded. Check the query logic and execution")
        failed_table.append(table_name)
    else:
        logging.info(f"[{table_name}] :Ingestion completed.Total Records: {row_count}.\
        Time taken: {round(end-start,2)} seconds")
    
# =========================== Data Ingestion Process ===========================
# ------------------------------------------------------------------------------

table_names_list = ["begin_inventory", "end_inventory", "purchase_prices", 
               "vendor_invoice", "purchases", "sales"]

table_config = [
    {
        "table_name" : "begin_inventory",
        "file_name"  : "begin_inventory.csv",
        "columns"    : ['InventoryId','Store','City','ProductId',
                        'Description','Size','onHand','Price','startDate'],
        "date_col"   : ['startDate']
    },
    {
        "table_name" : "end_inventory",
        "file_name"  : "end_inventory.csv",
        "columns"    : ['InventoryId','Store','City','ProductId',
                        'Description','Size','onHand','Price','endDate'],
        "date_col"   : ['endDate']
    },
    {
        "table_name" : "purchase_prices",
        "file_name"  : "purchase_prices.csv",
        "columns"    : ['ProductId', 'Description', 'Price', 'Size', 'Volume', 'Classification',
                        'PurchasePrice', 'VendorNumber', 'VendorName'],
        "date_col"   : None
    },
    {
        "table_name" : "vendor_invoice",
        "file_name"  : "vendor_invoice.csv",
        "columns"    : ['VendorNumber', 'VendorName', 'InvoiceDate', 'PONumber', 'PODate',
                        'PayDate', 'Quantity', 'Dollars', 'Freight', 'Approval'],
        "date_col"   : ['InvoiceDate','PODate','PayDate']
    },
    {
        "table_name" : "purchases",
        "file_name"  : "purchases.csv",
        "columns"    : ['InventoryId', 'Store', 'ProductId', 'Description', 'Size', 'VendorNumber',
                        'VendorName', 'PONumber', 'PODate', 'ReceivingDate', 'InvoiceDate',
                        'PayDate', 'PurchasePrice', 'Quantity', 'Dollars', 'Classification'],
        "date_col"   : ['PODate', 'ReceivingDate', 'InvoiceDate','PayDate']
    },
    {
        "table_name" : "sales",
        "file_name"  : "sales.csv",
        "columns"    : ['InventoryId', 'Store', 'ProductId', 'Description', 'Size', 'SalesQuantity',
                        'SalesDollars', 'SalesPrice', 'SalesDate', 'Volume', 'Classification',
                        'ExciseTax', 'VendorNo', 'VendorName'],
        "date_col"   : ['SalesDate']
    }
    ]

if __name__ == "__main__":
    final_start = time.time()

    # Create database engine connection to "inventory_db" database
    conn_eng = None
    try:
        database_url = URL.create (
            drivername = "mysql+pymysql",
            username = DB_USER,
            host = DB_HOST,
            password = DB_PASSWORD,
            database = "inventory_db"
        )
        conn_eng = create_engine(database_url, connect_args={"local_infile": 1})

        with conn_eng.connect() as conn:
            conn.execute(text("select 1;"))

        logging.info("<<< Database Connection Established >>>")

        logging.info("Data Ingestion Started :")
        failed_table = []
    
        for t in table_config :
            try:
                file_path = BASE_DIR/"datasets"/t['file_name']
                data_ingestion_func(
                    table_name = t['table_name'],
                    file_path = file_path,
                    columns = t['columns'],
                    date_col = t['date_col'])
                
            except (FileNotFoundError,ValueError) as e:
                logging.error(f"[{t['table_name']}] : {e}")
                failed_table.append(t['table_name'])

            except SQLAlchemyError as e:
                logging.exception(f"[{t['table_name']}] : Database Error during ingestion")
                failed_table.append(t['table_name'])
                
            except Exception as e:
                logging.exception(f"[{t['table_name']}] : Unexpected Error during ingestion")
                failed_table.append(t['table_name'])

    except SQLAlchemyError as e:
        logging.exception("Database Error : Failed to establish database connection")
        raise

    except Exception as e:
        logging.exception("Unexpected Error : Failed to establish database connection")
        raise


    finally:
        
        final_end =time.time()
        if failed_table :
            logging.warning(f"Ingestion Complete with Failures : {failed_table}.\
            Total time taken: {round(final_end-final_start,2)} seconds")
        else:
            logging.info(f"Ingestion Complete for all tables.\
            Total time taken: {round(final_end-final_start,2)} seconds")
            
        if conn_eng:
            conn_eng.dispose()
            logging.info("xxx  Database Connection closed  xxx")

# ---------------------------------------------------------------------------------------