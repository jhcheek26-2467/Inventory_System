SOURCE: All sheet of Partender Excel export

PRODUCTS TABLE
Excel Column              → DB Column
─────────────────────────────────────
Product Name              → product_name
Product Code (as text)    → product_code
Bin Number (as text)      → bin_number
Container Size (mL)       → container_size_ml
Wholesale Cost/Unit ($)   → wholesale_cost_per_unit
Avg Retail Price/Serving  → avg_retail_price_per_serving
[Distributor lookup]      → distributor_id
[Category lookup]         → category_id

DISTRIBUTORS TABLE
Excel Column              → DB Column
─────────────────────────────────────
Distributor               → distributor_name

CATEGORIES TABLE
Excel Column              → DB Column
─────────────────────────────────────
Selected Product Category → category_name

INVENTORY_SNAPSHOTS TABLE
Excel Column              → DB Column
─────────────────────────────────────
[from filename]           → snapshot_date
[product lookup]          → product_id
[location lookup]         → location_id
Circle Bar Quantity       → quantity (location: Circle Bar)
Main Bar Quantity         → quantity (location: Main Bar)
Garage Bar Quantity       → quantity (location: Garage Bar)
Ice Bar Quantity          → quantity (location: Ice Bar)
Rooftop Bar Quantity      → quantity (location: Rooftop Bar)
Jungle Bar Quantity       → quantity (location: Jungle Bar)
Dry Storage Quantity      → quantity (location: Dry Storage)
VIP Quantity              → quantity (location: VIP)
BIBs Quantity             → quantity (location: BIBs)
DO NOT TOUCH Quantity     → quantity (location: DO NOT TOUCH)

COLUMNS INTENTIONALLY IGNORED
─────────────────────────────────────
Total Quantity On-Hand    → calculated, not stored
Wholesale Value On-Hand   → calculated, not stored
Total Servings On-Hand    → calculated, not stored
Par                       → not stored yet (future milestone)
Need for Par              → calculated, not stored
Retail Value On-Hand      → calculated, not stored
Product Category Tier 1/2/3 → Selected Product Category used instead