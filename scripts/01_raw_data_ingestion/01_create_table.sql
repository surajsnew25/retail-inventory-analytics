/* 
----------------------------------------------------------------------------------------
 Script: Inventory Database Initialization

 Purpose:
 - Create the database 'inventory_db' if it does not already exist
 - Reset the schema by dropping existing tables (if present)
 - Define and create all core tables with their respective structures

 Scope:
 - Covers base schema setup for inventory, purchases, sales, product and vendor data
 - Intended as the foundational (DDL) layer of the data pipeline

 Notes:
 - Safe to re-run due to use of 'IF EXISTS' and 'IF NOT EXISTS'
 - Designed for initial setup and schema reinitialization
-----------------------------------------------------------------------------------------
*/

-- Create database
create database if not exists inventory_db ;
use inventory_db;

-- =============================================================

-- Create begin inventory table
drop table if exists begin_inventory;  -- drop table if already exists
create table begin_inventory (         -- create fresh table
	InventoryId varchar(40),
    Store int,
    City varchar(40),
    ProductId int,
    Description varchar(100),
    Size varchar(20),
    onHand int,
    Price decimal(10,2),
    startDate date
);

-- Create end inventory table
drop table if exists end_inventory;
create table end_inventory (
	InventoryId varchar(40),
    Store int,
    City varchar(40),
    ProductId int,
    Description varchar(100),
    Size varchar(20),
    onHand int,
    Price decimal(10,2),
    endDate date
);

-- Create Purchase Prices table
drop table if exists purchase_prices;
create table purchase_prices (
	ProductId int,
    Description varchar(100),
    Price decimal(10,2),
    Size varchar(20),
    Volume int,
    Classification int,
    PurchasePrice decimal(10,2),
    VendorNumber int,
    VendorName varchar(100)
);

-- Create Vendor Invoice table
drop table if exists vendor_invoice;
create table vendor_invoice (
	VendorNumber int,
    VendorName varchar(100),
    InvoiceDate	date,
    PONumber int,
    PODate date,
    PayDate	date,
    Quantity int,
    Dollars	decimal(10,2),
    Freight	decimal(10,2),
    Approval varchar(20)
);

-- Create Purchase transactions table
drop table if exists purchases;
create table purchases (
	InventoryId varchar(40),
    Store int,
    ProductId int,
    Description	varchar(100),
    Size varchar(20),
    VendorNumber int,
    VendorName varchar(40),
    PONumber int,
    PODate date,
    ReceivingDate date,
    InvoiceDate	date,
    PayDate	date,
    PurchasePrice decimal(10,2),
    Quantity int,
    Dollars	decimal(10,2),
    Classification int
);

-- Create Sales transactions table
drop table if exists sales;
create table sales (
	InventoryId	varchar(40),
    Store int,
    ProductId int,
    Description varchar(100),
    Size varchar(20),
    SalesQuantity int,
    SalesDollars  decimal(10,2),
    SalesPrice decimal(10,2),
    SalesDate date,
    Volume	int,
    Classification int,
    ExciseTax decimal(10,2),
    VendorNo int,
    VendorName varchar(40)
);

-- =============================================================



