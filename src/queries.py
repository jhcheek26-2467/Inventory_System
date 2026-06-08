import pandas as pd
from sqlalchemy import text


def get_inventory_value_by_product(conn, snapshot_date):
    """
    Total wholesale value on hand per product for one snapshot date.

    SQL: For each product, multiply quantity at each location by that
    product's wholesale cost per unit, add those amounts together, and
    sort products from most to least valuable on hand.
    """
    query = text(
        """
        SELECT
            p.product_id,
            p.product_name,
            SUM(s.quantity * COALESCE(p.wholesale_cost_per_unit, 0)) AS wholesale_value_on_hand
        FROM inventory_snapshots AS s
        INNER JOIN products AS p ON p.product_id = s.product_id
        WHERE s.snapshot_date = :snapshot_date
        GROUP BY p.product_id, p.product_name
        ORDER BY wholesale_value_on_hand DESC
        """
    )
    return pd.read_sql(query, conn, params={"snapshot_date": snapshot_date})


def get_inventory_value_by_location(conn, snapshot_date):
    """
    Total wholesale value on hand per location for one snapshot date.

    SQL: For each bar or storage location, multiply every product's
    quantity at that location by its wholesale cost, sum those amounts,
    and sort locations from highest to lowest value on hand.
    """
    query = text(
        """
        SELECT
            l.location_id,
            l.location_name,
            SUM(s.quantity * COALESCE(p.wholesale_cost_per_unit, 0)) AS wholesale_value_on_hand
        FROM inventory_snapshots AS s
        INNER JOIN products AS p ON p.product_id = s.product_id
        INNER JOIN locations AS l ON l.location_id = s.location_id
        WHERE s.snapshot_date = :snapshot_date
        GROUP BY l.location_id, l.location_name
        ORDER BY wholesale_value_on_hand DESC
        """
    )
    return pd.read_sql(query, conn, params={"snapshot_date": snapshot_date})


def get_inventory_value_by_category(conn, snapshot_date):
    """
    Total wholesale value on hand per product category for one snapshot date.

    SQL: Roll up all snapshot rows through each product's category,
    multiply quantity by wholesale cost, sum by category, and sort
    highest to lowest. Products with no category are grouped as
    'Uncategorized'.
    """
    query = text(
        """
        SELECT
            p.category_id,
            COALESCE(c.category_name, 'Uncategorized') AS category_name,
            SUM(s.quantity * COALESCE(p.wholesale_cost_per_unit, 0)) AS wholesale_value_on_hand
        FROM inventory_snapshots AS s
        INNER JOIN products AS p ON p.product_id = s.product_id
        LEFT JOIN categories AS c ON c.category_id = p.category_id
        WHERE s.snapshot_date = :snapshot_date
        GROUP BY p.category_id, COALESCE(c.category_name, 'Uncategorized')
        ORDER BY wholesale_value_on_hand DESC
        """
    )
    return pd.read_sql(query, conn, params={"snapshot_date": snapshot_date})


def get_inventory_value_by_distributor(conn, snapshot_date):
    """
    Total wholesale value on hand per distributor for one snapshot date.

    SQL: Same value calculation as the other rollups, but grouped by
    the distributor linked on each product. Products with no distributor
    are grouped as 'No distributor listed'.
    """
    query = text(
        """
        SELECT
            p.distributor_id,
            COALESCE(d.distributor_name, 'No distributor listed') AS distributor_name,
            SUM(s.quantity * COALESCE(p.wholesale_cost_per_unit, 0)) AS wholesale_value_on_hand
        FROM inventory_snapshots AS s
        INNER JOIN products AS p ON p.product_id = s.product_id
        LEFT JOIN distributors AS d ON d.distributor_id = p.distributor_id
        WHERE s.snapshot_date = :snapshot_date
        GROUP BY p.distributor_id, COALESCE(d.distributor_name, 'No distributor listed')
        ORDER BY wholesale_value_on_hand DESC
        """
    )
    return pd.read_sql(query, conn, params={"snapshot_date": snapshot_date})


def get_below_par_products(conn, snapshot_date):
    """
    Products whose total quantity across all locations is below par.

    SQL: Add up quantity for each product on the given date, compare that
    total to the product's par level, and return only products where the
    total is less than par. Also shows how many units are needed to reach par.

    Requires a par column on the products table (not imported yet).
    """
    query = text(
        """
        SELECT
            p.product_id,
            p.product_name,
            SUM(s.quantity) AS total_quantity_on_hand,
            p.par,
            p.par - SUM(s.quantity) AS need_for_par
        FROM inventory_snapshots AS s
        INNER JOIN products AS p ON p.product_id = s.product_id
        WHERE s.snapshot_date = :snapshot_date
          AND p.par IS NOT NULL
        GROUP BY p.product_id, p.product_name, p.par
        HAVING SUM(s.quantity) < p.par
        ORDER BY need_for_par DESC
        """
    )
    return pd.read_sql(query, conn, params={"snapshot_date": snapshot_date})


def get_available_snapshot_dates(conn):
    """
    All snapshot dates in the database, oldest first.

    SQL: Select each distinct snapshot_date from inventory_snapshots
    and sort them in chronological order.
    """
    query = text(
        """
        SELECT DISTINCT snapshot_date
        FROM inventory_snapshots
        ORDER BY snapshot_date ASC
        """
    )
    return pd.read_sql(query, conn)
