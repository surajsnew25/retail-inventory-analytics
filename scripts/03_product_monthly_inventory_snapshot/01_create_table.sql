/*
------------------------------------------------------------------------------------------------
Script: Product Monthly Inventory Table Creation

Purpose:
- Create the 'product_monthly_inventory' table in the 'inventory_db'
- Store month level inventory movement metrics for each product
- Enable analysis of stock flow, inventory trends, and turnover behavior

Scope:
- Defines schema for an analytical table (monthly aggregation level)
- Captures key inventory metrics: opening stock, purchases, sales, and closing stock

Notes:
- Table is recreated on each run using 'DROP TABLE IF EXISTS'
- Represents a transformation layer in the data pipeline (post-ingestion)
-------------------------------------------------------------------------------------------------
*/

-- Create Product Summary table
drop table if exists inventory_db.product_monthly_inventory;  -- drop table if already exists
create table inventory_db.product_monthly_inventory(         -- create fresh table
    ProductId int,
    month_startdate date,
    OpeningStock int,
    PurchaseQuantity int,
    SalesQuantity int,
	ClosingStock int
);

-- -----------------------------------------------------------