/*
--------------------------------------------------------------------------------------------------------
Script: Product Summary Table Creation

Purpose:
- Create the 'product_summary' table in the 'inventory_db'
- Store aggregated product level metrics derived from transactional data
- Support downstream analysis such as product performance, profitability, and pricing insights

Scope:
- Defines schema for a curated analytical table (not raw data layer)
- Intended to hold pre-aggregated metrics across purchases and sales

Notes:
- Table is recreated on each run using 'DROP TABLE IF EXISTS'
- Represents a transformation layer in the data pipeline (post-ingestion)
--------------------------------------------------------------------------------------------------------        
*/

-- Create Product Summary table
drop table if exists inventory_db.product_summary;  -- drop table if already exists
create table inventory_db.product_summary (         -- create fresh table
    ProductId int,
    Description varchar(100),
    VendorNumber int,
    VendorName varchar(100),
    Volume_ml int,
    ActualPrice decimal(10,2),
    PurchasePrice decimal(10,2),
    TotalQuantityPurchased int,
	TotalPurchaseDollars decimal(12,2),
	SalesPrice decimal(10,2),
	TotalQuantitySold int,
	TotalSalesDollars decimal(12,2),
    GrossProfit decimal(12,2),
    GrossProfitMargin decimal(6,2)
);

-- -----------------------------------------------------------