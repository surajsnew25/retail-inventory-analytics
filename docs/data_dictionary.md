# Data Dictionary

## Core Tables
### 🧾 Table: begin_inventory
- Purpose : Captures the opening stock quantity and value for each SKU at each store as of 1 Jan 2024, forming the baseline for all inventory analysis.

- Columns :

| Column Name  | Data Type        | Description |
|--------------|-----------------|-------------|
| InventoryId  | varchar(40)     | Unique identifier for each inventory record |
| Store        | int             | Store identifier where the inventory is held |
| City         | varchar(40)     | City in which the store is located |
| ProductId    | int             | Unique identifier for each SKU (combination of product description, size, and vendor) |
| Description  | varchar(100)    | Product name or description |
| Size         | varchar(20)     | Product size or packaging details |
| onHand       | int             | Quantity of product available at the start of the period |
| Price        | decimal(10,2)   | Unit price of the product |
| startDate    | date            | Inventory snapshot date (fixed as 2024-01-01) |

---

### 🧾 Table: end_inventory
- Purpose : Captures the closing stock quantity and value for each SKU at each store as of 31 Dec 2024, enabling period-end inventory valuation and comparison with opening stock.

- Columns :

| Column Name  | Data Type        | Description |
|--------------|-----------------|-------------|
| InventoryId  | varchar(40)     | Unique identifier for each inventory record |
| Store        | int             | Store identifier where the inventory is held |
| City         | varchar(40)     | City in which the store is located |
| ProductId    | int             | Unique identifier for each SKU (combination of product description, size, and vendor) |
| Description  | varchar(100)    | Product name or description |
| Size         | varchar(20)     | Product size or packaging details |
| onHand       | int             | Quantity of product available at the end of the period |
| Price        | decimal(10,2)   | Unit price of the product |
| endDate      | date            | Inventory snapshot date (fixed as 2024-12-31) |

---

### 🧾 Table: purchase_prices
- Purpose : Stores vendor-level procurement cost and pricing details for each SKU, enabling cost analysis, margin evaluation, and vendor comparison.

- Columns :

| Column Name    | Data Type        | Description |
|----------------|-----------------|-------------|
| ProductId      | int             | Unique identifier for each SKU (combination of product description, size, and vendor) |
| Description    | varchar(100)    | Product name or description |
| Price          | decimal(10,2)   | Selling price of the product |
| Size           | varchar(20)     | Product size or packaging details |
| Volume         | int             | Product volume in ml |
| Classification | int             | Product category or classification code |
| PurchasePrice  | decimal(10,2)   | Unit cost at which the product is procured from the vendor |
| VendorNumber   | int             | Unique identifier for the vendor |
| VendorName     | varchar(100)    | Name of the vendor supplying the product |

---

### 🧾 Table: vendor_invoice
- Purpose : Captures procurement transactions from vendors, including quantities, costs, freight, and payment details, enabling spend tracking and vendor performance analysis.

- Columns :

| Column Name  | Data Type        | Description |
|--------------|-----------------|-------------|
| VendorNumber | int             | Unique identifier for the vendor |
| VendorName   | varchar(100)    | Name of the vendor |
| InvoiceDate  | date            | Date when the invoice was issued |
| PONumber     | int             | Purchase order number linked to the invoice |
| PODate       | date            | Date when the purchase order was created |
| PayDate      | date            | Date when the invoice payment was made |
| Quantity     | int             | Total quantity of items purchased in the invoice |
| Dollars      | decimal(10,2)   | Total invoice amount excluding freight |
| Freight      | decimal(10,2)   | Transportation or shipping cost associated with the invoice |
| Approval     | varchar(20)     | Approval status of the invoice (e.g., approved, pending) |

---

### 🧾 Table: purchases
- Purpose : Captures SKU-level procurement transactions, linking inventory, vendor, and purchase order details to enable detailed cost, quantity, and procurement flow analysis.

- Columns :

| Column Name    | Data Type        | Description |
|----------------|-----------------|-------------|
| InventoryId    | varchar(40)     | Unique identifier for each inventory record |
| Store          | int             | Store where the inventory is received |
| ProductId      | int             | Unique identifier for each SKU (combination of product description, size, and vendor) |
| Description    | varchar(100)    | Product name or description |
| Size           | varchar(20)     | Product size or packaging details |
| VendorNumber   | int             | Unique identifier for the vendor |
| VendorName     | varchar(40)     | Name of the vendor |
| PONumber       | int             | Purchase order number |
| PODate         | date            | Date when the purchase order was created |
| ReceivingDate  | date            | Date when the inventory was received |
| InvoiceDate    | date            | Date when the invoice was issued |
| PayDate        | date            | Date when payment was made to the vendor |
| PurchasePrice  | decimal(10,2)   | Unit cost of the product purchased |
| Quantity       | int             | Number of units purchased |
| Dollars        | decimal(10,2)   | Total purchase amount (Quantity × PurchasePrice) |
| Classification | int             | Product category or classification code |

---

### 🧾 Table: sales
- Purpose : Captures SKU-level sales transactions, including quantity, revenue, pricing, and tax details, enabling revenue, demand, and margin analysis.

- Columns :

| Column Name     | Data Type        | Description |
|-----------------|-----------------|-------------|
| InventoryId     | varchar(40)     | Unique identifier for each inventory record |
| Store           | int             | Store where the sale occurred |
| ProductId       | int             | Unique identifier for each SKU (combination of product description, size, and vendor) |
| Description     | varchar(100)    | Product name or description |
| Size            | varchar(20)     | Product size or packaging details |
| SalesQuantity   | int             | Number of units sold |
| SalesDollars    | decimal(10,2)   | Total revenue generated from sales |
| SalesPrice      | decimal(10,2)   | Unit selling price of the product |
| SalesDate       | date            | Date when the sale occurred |
| Volume          | int             | Product volume in ml |
| Classification  | int             | Product category or classification code |
| ExciseTax       | decimal(10,2)   | Tax applied on the sale |
| VendorNo        | int             | Unique identifier for the vendor |
| VendorName      | varchar(40)     | Name of the vendor associated with the product |

---

## Derived Tables
### 🧾 Table: product_summary
- Purpose : Aggregates SKU-level purchase and sales data to evaluate overall performance, including volume, revenue, cost, and profitability.

- Columns :

| Column Name            | Data Type        | Description |
|------------------------|-----------------|-------------|
| ProductId              | int             | Unique identifier for each SKU (combination of product description, size, and vendor) |
| Description            | varchar(100)    | Product name or description |
| VendorNumber           | int             | Unique identifier for the vendor |
| VendorName             | varchar(100)    | Name of the vendor |
| Volume_ml              | int             | Product volume in ml |
| ActualPrice            | decimal(10,2)   | Listed selling price of the product |
| PurchasePrice          | decimal(10,2)   | Unit cost of the product |
| TotalQuantityPurchased | int             | Total units purchased over the period |
| TotalPurchaseDollars   | decimal(12,2)   | Total procurement cost (Quantity Purchased × Purchase Price) |
| SalesPrice             | decimal(10,2)   | Derived selling price |
| TotalQuantitySold      | int             | Total units sold over the period |
| TotalSalesDollars      | decimal(12,2)   | Total revenue generated from sales |
| GrossProfit            | decimal(12,2)   | Gross profit (Total Sales Dollars − Cost of Goods Sold (COGS)) |
| GrossProfitMargin      | decimal(6,2)    | Profit Margin (Gross Profit*100  ÷ Total Sales Dollars) expressed as a percentage |

---

### 🧾 Table: product_monthly_inventory
- Purpose : Tracks monthly stock movement for each SKU, capturing opening balance, purchases, sales, and closing stock to analyze inventory flow and turnover.

- Columns :

| Column Name      | Data Type | Description |
|------------------|----------|-------------|
| ProductId        | int      | Unique identifier for each SKU (combination of product description, size, and vendor) |
| month_startdate  | date     | Start date of the month representing the reporting period |
| OpeningStock     | int      | Quantity available at the beginning of the month |
| PurchaseQuantity | int      | Total quantity purchased during the month |
| SalesQuantity    | int      | Total quantity sold during the month |
| ClosingStock     | int      | Quantity remaining at the end of the month |

---