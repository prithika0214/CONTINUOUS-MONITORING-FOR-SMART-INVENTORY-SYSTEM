import csv
import random
import datetime

headers = [
    "product_id", "product_name", "category", "brand", "unit", "price_inr",
    "quantity", "minimum_stock", "supplier", "last_updated_ist"
]

products = [
    ("Tea Powder", "Beverages", "250g pack"),
    ("Milk Powder", "Milk & Dairy", "500g pack"),
    ("Full Cream Milk", "Milk & Dairy", "1L"),
    ("Wheat", "Rice, Pulses & Grains", "1kg"),
    ("Appalam", "Packaged Food", "pack"),
    ("Fruit Juice", "Beverages", "1L bottle"),
    ("Fish", "Meat, Fish & Eggs", "1kg"),
    ("Flavoured Milk", "Milk & Dairy", "200ml bottle"),
    ("Papaya", "Fresh Fruits", "1kg"),
    ("Jam", "Packaged Food", "500g jar"),
    ("Brinjal", "Fresh Vegetables", "1kg")
]

brands = ["Amul", "Aashirvaad", "Nandini", "Heritage", "Milky Mist", "Local", "Tata", "Lipton"]
suppliers = ["Salem Wholesale Hub", "Tiruchirappalli Food Supply", "Sri Lakshmi Traders", "Chennai Wholesale Foods"]

output_path = r"c:\Users\DELL\Desktop\SIMS\data\stockpulse_indian_grocery_dataset.csv"

def generate_row(i):
    prod = random.choice(products)
    prod_id = f"TNF{i:04d}"
    prod_name, cat, unit = prod
    brand = random.choice(brands)
    price = round(random.uniform(20.0, 500.0), 2)
    stock = random.randint(0, 350)
    reorder = random.randint(10, 80)
    supp = random.choice(suppliers)
    last_upd = datetime.date.today().strftime("%Y-%m-%d %H:%M:%S")

    return [
        prod_id, prod_name, cat, brand, unit, price, stock, reorder, supp, last_upd
    ]

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    for i in range(1, 1001):
        writer.writerow(generate_row(i))

print("Generated 1000 rows of dataset successfully.")
