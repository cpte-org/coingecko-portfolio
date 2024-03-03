import tkinter as tk
from tkinter import ttk
import requests
import json
from dotenv import load_dotenv
import os
import pickle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from datetime import datetime
from tabulate import tabulate
import argparse

# Load environment variables from .env file
load_dotenv()

# Global variable for cached data
CACHE_FILE = "cached_data.dat"
PORTFOLIO_FILE = "portfolio.json"
cached_data = {}
portfolio_data = {}

# Variable to store the active portfolio ID
active_portfolio_id = None


def load_cached_data():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    return {}


def save_cached_data():
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cached_data, f)


def load_portfolio_data():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return {}


def save_portfolio_data():
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio_data, f, indent=4)


cached_data = load_cached_data()
portfolio_data = load_portfolio_data()


def fetch_data(coin, use_savings=True):
    global cached_data

    # Check if data is cached
    if coin in cached_data:
        return cached_data[coin]

    # Check if the coin is a stable coin
    stable_coin_list = [
        "usdd",
        "usd-coin",
        "tether",
        "dai",
        "husd",
        "tusd",
        "busd",
        "aave-v3-usdt",
    ]
    if use_savings and coin.lower() in stable_coin_list:
        cached_data[coin] = (1.0, 0.0, 0.0, 0.0)
        save_cached_data()
        return cached_data[coin]

    url = f"https://api.coingecko.com/api/v3/coins/{coin}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"

    # Check if to use API key or not
    if use_savings:
        # Try fetching without API key first
        response = requests.get(url)
        if response.status_code == 429:  # Rate limit exceeded
            # If rate limit exceeded, use the API key
            headers = {"x-cg-demo-api-key": os.getenv("API_KEY")}
            response = requests.get(url, headers=headers)
    else:
        # Fetch directly with API key
        headers = {"x-cg-demo-api-key": os.getenv("API_KEY")}
        response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        # Cache the data
        cached_data[coin] = (
            data["market_data"]["current_price"]["usd"],
            data["market_data"]["price_change_percentage_1h_in_currency"]["usd"],
            data["market_data"]["price_change_percentage_24h_in_currency"]["usd"],
            data["market_data"]["price_change_percentage_7d_in_currency"]["usd"],
        )
        save_cached_data()  # Save cached data to file
        return cached_data[coin]
    else:
        print(f"Failed to fetch data for {coin}.")
        return None, None, None, None


def calculate_portfolio_value(portfolio, use_savings=True):
    total_value = 0
    for coin, quantity in portfolio.items():
        price, _, _, _ = fetch_data(coin, use_savings)
        if price is not None:
            total_value += price * quantity
    return total_value


def generate_pdf_report(portfolio_id, use_savings=True):
    if portfolio_id not in portfolio_data:
        print("Error: Portfolio ID not found.")
        return

    portfolio = portfolio_data[portfolio_id]

    # Generate file name with current date
    file_name = f"portfolio_report_{portfolio_id}.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=letter)
    data = [["Coin", "Price", "1h Change", "24h Change", "7d Change", "Quantity", "Value"]]

    for coin, quantity in portfolio.items():
        price, change_1h, change_24h, change_7d = fetch_data(coin, use_savings)
        price = price if price is not None else "Price not available"
        change_1h = f"{change_1h:.2f}%" if change_1h is not None else "N/A"
        change_24h = f"{change_24h:.2f}%" if change_24h is not None else "N/A"
        change_7d = f"{change_7d:.2f}%" if change_7d is not None else "N/A"
        coin_value = price * quantity if isinstance(price, float) else "Value not available"
        data.append([coin, f"${price:.2f}", change_1h, change_24h, change_7d, str(quantity), f"${coin_value:.2f}"])

    # Add total portfolio value
    total_value = calculate_portfolio_value(portfolio, use_savings)
    data.append(["", "", "", "", "", "Total Portfolio Value", f"${total_value:.2f}"])

    # Add date
    data.append(["", "", "", "", "", "Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    # Create table
    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -2), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    # Add table to document
    doc.build([table])

def display_portfolio(portfolio_id, use_savings=True):
    if portfolio_id not in portfolio_data:
        print("Error: Portfolio ID not found.")
        return

    portfolio = portfolio_data[portfolio_id]

    def sort_column(tree, col, reverse):
        l = [(float(tree.set(k, col)), k) for k in tree.get_children("")]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            tree.move(k, "", index)

        tree.heading(col, command=lambda: sort_column(tree, col, not reverse))

    root = tk.Tk()
    root.title("Portfolio Display")

    title_label = tk.Label(root, text="Coingecko Portfolio", font=("Helvetica", 16, "bold"))
    title_label.pack()

    total_value_label = tk.Label(
        root,
        text=f"Total Portfolio Value: ${calculate_portfolio_value(portfolio, use_savings):.2f}",
        font=("Helvetica", 12),
    )
    total_value_label.pack()

    tree = ttk.Treeview(
        root, columns=("Coin", "Price", "1h Change", "24h Change", "7d Change", "Quantity", "Value")
    )
    tree.heading("#0", text="Coin", command=lambda: sort_column(tree, "#0", False))
    tree.heading("#1", text="Price", command=lambda: sort_column(tree, "#1", False))
    tree.heading("#2", text="1h Change", command=lambda: sort_column(tree, "#2", False))
    tree.heading("#3", text="24h Change", command=lambda: sort_column(tree, "#3", False))
    tree.heading("#4", text="7d Change", command=lambda: sort_column(tree, "#4", False))
    tree.heading("#5", text="Quantity", command=lambda: sort_column(tree, "#5", False))
    tree.heading("#6", text="Value", command=lambda: sort_column(tree, "#6", False))

    for coin, quantity in portfolio.items():
        price, change_1h, change_24h, change_7d = fetch_data(coin, use_savings)

        if price is not None and all(
            change is not None for change in [change_1h, change_24h, change_7d]
        ):
            coin_value = price * quantity
        else:
            price = price if price is not None else "Price not available"
            change_1h = f"{change_1h:.2f}%" if change_1h is not None else "N/A"
            change_24h = f"{change_24h:.2f}%" if change_24h is not None else "N/A"
            change_7d = f"{change_7d:.2f}%" if change_7d is not None else "N/A"
            coin_value = (
                price * quantity if price is not None else "Value not available"
            )
        tree.insert(
            "",
            "end",
            text=coin,
            values=(price, change_1h, change_24h, change_7d, quantity, coin_value),
        )

    tree.pack(expand=True, fill="both")
    root.mainloop()


def switch_portfolio(portfolio_id):
    global active_portfolio_id
    active_portfolio_id = portfolio_id
    print(f"Active portfolio switched to: {portfolio_id}")


def main():
    global active_portfolio_id

    parser = argparse.ArgumentParser(description="Coingecko Portfolio Manager")
    parser.add_argument("--savings", type=str, default="true", help="Enable or disable API calls savings (true/false)")
    args = parser.parse_args()

    use_savings = args.savings.lower() != "false"

    while True:
        print("\n-----------------------------")
        print("  Coingecko Portfolio")
        print("-----------------------------\n")

        print("1. Refresh Portfolio Data")
        print("2. Generate PDF Report")
        print("3. Display Portfolio (GUI)")
        print("4. Switch Active Portfolio")
        print("5. Exit")

        choice = input("Enter your choice: ")
        if choice == "1":
            print("Available Portfolio IDs:")
            for index, portfolio_id in enumerate(portfolio_data, start=1):
                print(f"{index}. {portfolio_id}")
            portfolio_choice = int(input("Choose Portfolio Number: "))
            if portfolio_choice < 1 or portfolio_choice > len(portfolio_data):
                print("Error: Invalid Portfolio Number.")
                continue
            portfolio_id = list(portfolio_data.keys())[portfolio_choice - 1]

            portfolio = portfolio_data[portfolio_id]

            # Clear cached data
            global cached_data
            cached_data = {}
            # Initialize a list to store the data
            table_data = []

            # Iterate through the portfolio
            for coin, quantity in portfolio.items():
                price, _, change_24h, _ = fetch_data(coin, use_savings)
                if price is not None:
                    coin_value = price * quantity
                    table_data.append([coin, quantity, f"${coin_value:.2f}", f"${price:.2f}", f"%{change_24h:.2f}"])
                else:
                    table_data.append([coin, quantity, "Price not available", "-", "-"])

            # Define headers for the table
            headers = ["Coin", "Quantity", "Value", "Price", "24h Change"]

            # Print the table
            print(tabulate(table_data, headers=headers, tablefmt="pretty"))

            total_value = calculate_portfolio_value(portfolio, use_savings)
            print(f"\nTotal Portfolio Value: ${total_value:.2f}\n")
            print("Portfolio data refreshed.")
        elif choice == "2":
            # Generate PDF report for the active portfolio
            if active_portfolio_id is None:
                print("Error: No active portfolio selected.")
                continue
            generate_pdf_report(active_portfolio_id, use_savings)
            print("PDF report generated successfully.")
        elif choice == "3":
            # Display portfolio GUI for the active portfolio
            if active_portfolio_id is None:
                print("Error: No active portfolio selected.")
                continue
            display_portfolio(active_portfolio_id, use_savings)
        elif choice == "4":
            # Switch active portfolio
            print("Available Portfolio IDs:")
            for index, portfolio_id in enumerate(portfolio_data, start=1):
                print(f"{index}. {portfolio_id}")
            portfolio_choice = int(input("Choose Portfolio Number: "))
            if portfolio_choice < 1 or portfolio_choice > len(portfolio_data):
                print("Error: Invalid Portfolio Number.")
                continue
            portfolio_id = list(portfolio_data.keys())[portfolio_choice - 1]
            switch_portfolio(portfolio_id)
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter a valid option.")


if __name__ == "__main__":
    main()
