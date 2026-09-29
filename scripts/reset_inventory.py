import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.database import get_db, load_grocery_dataset

def reset_inventory():
    print("WARNING: This will safely reset the inventory and load the Indian grocery dataset.")
    print("User accounts and authentications will NOT be deleted.")
    confirm = input("Type 'YES' to confirm: ")
    if confirm != "YES":
        print("Reset aborted.")
        return

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Delete old inventory to prevent duplicates (using replace=True in load_grocery_dataset)
        # But wait, load_grocery_dataset doesn't delete related records in transactions, stock_requests, sales_history.
        # We need to clear those first safely, or clear only demo data.
        
        # Clear child tables first
        cursor.execute("DELETE FROM sales_history")
        cursor.execute("DELETE FROM stock_requests")
        cursor.execute("DELETE FROM transactions")
        
        result = load_grocery_dataset(conn, replace=True)
        conn.commit()
        
        print(f"Success! Inserted {result['inserted']} grocery products from the new dataset.")
        print("All old demo transactions, requests, and sales history were cleared for safety.")
        
    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_inventory()
