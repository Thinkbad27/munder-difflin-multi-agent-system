import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################


# Set up and load your env parameters and instantiate your model.

import os
from dotenv import load_dotenv
from smolagents import OpenAIServerModel, ToolCallingAgent, tool

load_dotenv()
UDACITY_OPENAI_API_KEY = os.getenv("UDACITY_OPENAI_API_KEY")
assert UDACITY_OPENAI_API_KEY is not None, "UDACITY_OPENAI_API_KEY not found in .env"

model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    api_base="https://openai.vocareum.com/v1",
    api_key=UDACITY_OPENAI_API_KEY,
)


"""Set up tools for your agents to use, these should be methods that combine the database functions above
 and apply criteria to them to ensure that the flow of the system is correct."""

# Shared product-catalog reference given to agents that need to map free-text
# item descriptions to exact catalog names (create_transaction fails on any
# name that doesn't match exactly).
def _build_catalog_reference() -> str:
    lines = [
        f"- {item['item_name']} (category: {item['category']}, unit price: ${item['unit_price']:.2f})"
        for item in paper_supplies
    ]
    return "Full product catalog (46 items):\n" + "\n".join(lines)

CATALOG_REFERENCE = _build_catalog_reference()


# Tools for inventory agent

@tool
def check_stock(item_name: str, as_of_date: str) -> str:
    """
    Check the current stock level of a specific catalog item as of a given date.

    Args:
        item_name: The exact catalog name of the item to check (must match the
            official paper_supplies catalog name exactly).
        as_of_date: ISO-formatted date (YYYY-MM-DD) to check stock as of.
    """
    stock_df = get_stock_level(item_name, as_of_date)
    current_stock = int(stock_df["current_stock"].iloc[0])
    return f"{item_name}: {current_stock} units in stock as of {as_of_date}."


@tool
def check_full_inventory(as_of_date: str) -> str:
    """
    Retrieve the full snapshot of all items currently in stock (stock > 0) as of a given date.

    Args:
        as_of_date: ISO-formatted date (YYYY-MM-DD) to check inventory as of.
    """
    inventory = get_all_inventory(as_of_date)
    if not inventory:
        return f"No items currently in stock as of {as_of_date}."
    lines = [f"- {name}: {qty} units" for name, qty in sorted(inventory.items())]
    return f"Inventory as of {as_of_date}:\n" + "\n".join(lines)


@tool
def estimate_restock_arrival(request_date: str, quantity: int) -> str:
    """
    Estimate the delivery date if a restock order of a given quantity were
    placed with the supplier starting from a given date.

    Args:
        request_date: ISO-formatted date (YYYY-MM-DD) the restock order would be placed.
        quantity: Number of units to order from the supplier.
    """
    delivery_date = get_supplier_delivery_date(request_date, quantity)
    return f"An order of {quantity} units placed on {request_date} would arrive by {delivery_date}."


@tool
def place_restock_order(item_name: str, quantity: int, price: float, date: str) -> str:
    """
    Place a stock order with the supplier to replenish inventory. Compute
    price as the item's catalog unit price multiplied by quantity.

    Args:
        item_name: The exact catalog name of the item to restock.
        quantity: Number of units to order from the supplier.
        price: Total cost of this restock order (unit price x quantity).
        date: ISO-formatted date (YYYY-MM-DD) the order is placed.
    """
    transaction_id = create_transaction(
        item_name=item_name,
        transaction_type="stock_orders",
        quantity=quantity,
        price=price,
        date=date,
    )
    return f"Restock order placed (transaction id {transaction_id}): {quantity}x {item_name} for ${price:.2f}."


# Tools for quoting agent

@tool
def find_similar_past_quotes(search_terms: list, limit: int = 5) -> str:
    """
    Search historical quotes for similar past customer requests, to inform
    pricing and discount decisions for a new quote.

    Args:
        search_terms: List of keywords (item names, job type, event type) to
            search for in past requests and quote explanations.
        limit: Maximum number of past quotes to return.
    """
    results = search_quote_history(search_terms, limit=limit)
    if not results:
        return "No similar past quotes found."
    lines = []
    for r in results:
        lines.append(
            f"- ${r['total_amount']} | {r['job_type']} / {r['order_size']} / {r['event_type']} | "
            f"{r['quote_explanation']}"
        )
    return "Similar past quotes:\n" + "\n".join(lines)


@tool
def check_available_items(as_of_date: str) -> str:
    """
    Retrieve the full snapshot of all items currently in stock, to check
    what is actually available before quoting a price.

    Args:
        as_of_date: ISO-formatted date (YYYY-MM-DD) to check inventory as of.
    """
    inventory = get_all_inventory(as_of_date)
    if not inventory:
        return f"No items currently in stock as of {as_of_date}."
    lines = [f"- {name}: {qty} units" for name, qty in sorted(inventory.items())]
    return f"Inventory as of {as_of_date}:\n" + "\n".join(lines)


# Tools for ordering agent

@tool
def check_cash_health(as_of_date: str) -> str:
    """
    Check the company's current cash balance as of a given date, to confirm
    there is enough cash on hand before committing to a large restock or sale.

    Args:
        as_of_date: ISO-formatted date (YYYY-MM-DD) to check cash balance as of.
    """
    cash = get_cash_balance(as_of_date)
    return f"Cash balance as of {as_of_date}: ${cash:.2f}"


@tool
def get_financial_report(as_of_date: str) -> str:
    """
    Generate a full financial report (cash, inventory value, total assets)
    as of a given date, for internal reporting or health checks.

    Args:
        as_of_date: ISO-formatted date (YYYY-MM-DD) to generate the report as of.
    """
    report = generate_financial_report(as_of_date)
    return (
        f"Financial report as of {report['as_of_date']}: "
        f"cash=${report['cash_balance']:.2f}, "
        f"inventory_value=${report['inventory_value']:.2f}, "
        f"total_assets=${report['total_assets']:.2f}"
    )


@tool
def confirm_delivery_window(request_date: str, quantity: int) -> str:
    """
    Confirm the estimated delivery date for a given order quantity, to check
    whether it fits the customer's required timeline before finalizing a sale.

    Args:
        request_date: ISO-formatted date (YYYY-MM-DD) the order would be placed.
        quantity: Number of units in the order.
    """
    delivery_date = get_supplier_delivery_date(request_date, quantity)
    return f"An order of {quantity} units placed on {request_date} would be ready by {delivery_date}."


@tool
def finalize_sale(item_name: str, quantity: int, price: float, date: str) -> str:
    """
    Record a confirmed sales transaction for a customer order.

    Args:
        item_name: The exact catalog name of the item being sold.
        quantity: Number of units sold.
        price: Total price charged to the customer for this transaction.
        date: ISO-formatted date (YYYY-MM-DD) of the sale.
    """
    transaction_id = create_transaction(
        item_name=item_name,
        transaction_type="sales",
        quantity=quantity,
        price=price,
        date=date,
    )
    return f"Sale recorded (transaction id {transaction_id}): {quantity}x {item_name} for ${price:.2f}."


# Set up your agents and create an orchestration agent that will manage them.

inventory_agent = ToolCallingAgent(
    tools=[check_stock, check_full_inventory, estimate_restock_arrival, place_restock_order],
    model=model,
    name="inventory_agent",
    description=(
        "Handles all inventory questions: checking current stock levels for "
        "specific items or the full catalog, estimating supplier delivery "
        "timelines, and placing restock orders when stock is insufficient."
    ),
    instructions=f"""
You are the Inventory Agent for Munder Difflin Paper Company.

Your job: given an item name, quantity requested, and a date, determine
whether enough stock is available, and if not, whether restocking from the
supplier can arrive in time.

Process:
1. Use check_stock to see current stock for the requested item as of the
   request date. If the exact item name isn't obvious, match it to the
   closest name in the catalog below.
2. If current stock >= requested quantity, report that the item is available.
3. If not, use estimate_restock_arrival to see when a new order would arrive.
   Compute the restock price as (catalog unit price x quantity needed) and
   use place_restock_order to record the restock transaction.
4. Report back clearly: whether the item can be fulfilled, by when, and why.

IMPORTANT — no fabrication rule:
- Any stock number or delivery date you report MUST come verbatim from the
  return value of check_stock / estimate_restock_arrival. Never state a
  quantity or date from memory or general knowledge.
- If you have not called a tool for a fact, do not state that fact.

{CATALOG_REFERENCE}
""",
)

quoting_agent = ToolCallingAgent(
    tools=[find_similar_past_quotes, check_available_items],
    model=model,
    name="quoting_agent",
    description=(
        "Produces priced quotes for customer requests: maps free-text item "
        "descriptions to exact catalog names, checks past similar quotes for "
        "pricing precedent, and applies bulk discounts."
    ),
    instructions=f"""
You are the Quoting Agent for Munder Difflin Paper Company.

Your job: given a customer's free-text request (items, quantities, job type,
event type, order size), produce a priced quote.

Process:
1. Map each requested item description to the closest exact item name in the
   catalog below. Never invent an item name not in the catalog.
2. Use find_similar_past_quotes with relevant keywords (item names, job type,
   event type) to see how similar past orders were priced and discounted.
3. Use check_available_items to see what is currently in stock, for context.
4. Calculate a price using catalog unit prices, and apply a bulk discount
   for large orders (follow the pattern seen in similar past quotes).
5. Return: the exact item names and quantities, the unit prices, any
   discount applied and why, and the final total price.

IMPORTANT — arithmetic accuracy rule:
- The total price MUST equal (unit_price x quantity) for each item, summed,
  then adjusted for any discount you explicitly applied. Show this
  calculation before stating the final number.
- Never report a total of $0.00 unless every item's unit price is genuinely
  $0. Never report a total that you have not actually computed step by step.

{CATALOG_REFERENCE}
""",
)

sales_agent = ToolCallingAgent(
    tools=[check_cash_health, get_financial_report, confirm_delivery_window, finalize_sale],
    model=model,
    name="sales_agent",
    description=(
        "Finalizes customer orders: confirms delivery timelines and company "
        "cash health, then either records the sale or rejects the order with "
        "a clear reason (e.g. insufficient stock or an impossible deadline)."
    ),
    instructions="""
You are the Sales Agent for Munder Difflin Paper Company.

Your job: given a priced quote, an item's availability status (from the
Inventory Agent), and a requested delivery date, decide whether to finalize
the sale or reject the order.

Process:
1. Use confirm_delivery_window to check whether the item (already available,
   or after any restock) can be delivered by the customer's requested date.
2. For large orders, use check_cash_health and get_financial_report as a
   health check before committing.
3. If the order can be fulfilled by the required date: call finalize_sale to
   record the transaction, then report success with the transaction details.
4. If it cannot be fulfilled (insufficient stock and restock would arrive
   too late, or any other blocking reason): do NOT call finalize_sale.
   Clearly state the order is rejected and explain why in plain terms the
   customer can understand.

IMPORTANT — consistency rule:
- Never call finalize_sale unless your final report to the orchestrator says
  the order was fulfilled, and vice versa: if you call finalize_sale, your
  report MUST say it was fulfilled.
- The price you pass to finalize_sale MUST be exactly the total price given
  to you by the quoting step — do not invent or recompute a different number.
- Any delivery date you state MUST come verbatim from confirm_delivery_window's
  return value. Never state a date from your own knowledge (e.g. never output
  a year that doesn't match the request's actual timeframe).

IMPORTANT — proof-of-transaction rule:
- You may describe an order as "finalized" or "successful" ONLY if you
  actually called finalize_sale and it returned a transaction id. Your
  report MUST include that exact transaction id and the exact price from
  finalize_sale's return string.
- Never call finalize_sale with a price of $0.00. If quoting_agent could not
  produce a valid nonzero price, treat the order as rejected — do not
  finalize, and say a valid quote could not be produced.
- If you did not call finalize_sale, you MUST report the order as rejected
  or pending, never as successful.

""",
)

orchestrator = ToolCallingAgent(
    tools=[],
    model=model,
    managed_agents=[inventory_agent, quoting_agent, sales_agent],
    name="orchestrator",
    description="Top-level orchestrator for Munder Difflin customer requests.",
    instructions="""
You are the Orchestrator for Munder Difflin Paper Company's customer request
system. You do not have direct tools; you delegate to three specialist agents:

- inventory_agent: checks stock, estimates restock timing, places restock orders.
- quoting_agent: maps items to catalog names, checks quote history, prices the order.
- sales_agent: confirms delivery/cash health, finalizes or rejects the order.

For every customer request (which includes the request date), follow this
sequence:
1. Ask quoting_agent to interpret the request and produce a priced quote
   (exact item names, quantities, unit prices, discount, total).
2. Ask inventory_agent whether each requested item can be fulfilled by the
   request date (checking stock, restocking if needed).
3. Ask sales_agent to finalize or reject the order, based on the quote and
   the inventory availability/timeline findings.
4. Produce a final response to the customer that includes: the items and
   total price, whether the order was fulfilled or rejected, and a clear
   reason for the outcome. Do not include internal figures such as profit
   margins or raw error messages.

IMPORTANT — verbatim reporting rule:
- The price, item names, quantities, and delivery date in your final
  customer-facing response MUST be copied exactly as reported by
  quoting_agent / sales_agent. Do not recompute, round, or "improve" a number.
- Never state a date that a sub-agent did not explicitly report, and never
  use a date from your own general knowledge.
- If sales_agent rejected the order, the total price you report MUST be
  $0.00 and you must NOT describe any item as "successfully finalized."
- Before responding, sanity-check the total: does it look plausible given
  the quantity and catalog unit price? If a number looks obviously wrong
  (far too large, or $0 for a claimed "finalized" order), re-query the
  relevant agent instead of reporting it.

IMPORTANT — no unverified success claims:
- Only tell the customer an order was "successfully finalized" if
  sales_agent's report includes a transaction id and a nonzero price.
  If that proof is missing, report the order as rejected in your response
  to the customer, even if sales_agent's wording sounded positive.
- Your final response MUST always state the exact total price (and
  transaction id if finalized) — never omit the price for a "successful" order.

""",
)


def call_your_multi_agent_system(request_text: str) -> str:
    """Entry point used by run_test_scenarios() below."""
    result = orchestrator.run(request_text)
    return str(result)


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############

    # The orchestrator and its managed agents are already constructed at
    # module level above (see "Set up your agents..." section), so nothing
    # additional is needed here.

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############

        response = call_your_multi_agent_system(request_with_date)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
