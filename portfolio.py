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

# Load environment variables from .env file
load_dotenv()

# Global variable for cached data
CACHE_FILE = "cached_data.dat"
cached_data = {}

def load_cached_data():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_cached_data():
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cached_data, f)

cached_data = load_cached_data()

def fetch_data(coin):
    global cached_data
    
    # Check if data is cached
    if coin in cached_data:
        return cached_data[coin]

    # Check if the coin is a stable coin
    stable_coin_list = ["usdd", "usd-coin", "tether", "dai", "husd", "tusd", "busd", "aave-v3-usdt"]
    if coin.lower() in stable_coin_list:
        # Cache the stable coin data
        cached_data[coin] = (1.0, 0.0, 0.0, 0.0)  # Default values for stable coins
        save_cached_data()  # Save cached data to file
        return cached_data[coin]

    url = f"https://api.coingecko.com/api/v3/coins/{coin}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
    headers = {"x-cg-demo-api-key": os.getenv("API_KEY")}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        # Cache the data
        cached_data[coin] = (data['market_data']['current_price']['usd'],
                             data['market_data']['price_change_percentage_1h_in_currency']['usd'],
                             data['market_data']['price_change_percentage_24h_in_currency']['usd'],
                             data['market_data']['price_change_percentage_7d_in_currency']['usd'])
        save_cached_data()  # Save cached data to file
        return cached_data[coin]
    else:
        print(f"Failed to fetch data for {coin}.")
        return None, None, None, None


def calculate_portfolio_value(portfolio):
    total_value = 0
    for coin, quantity in portfolio.items():
        price, _, _, _ = fetch_data(coin)
        if price is not None:
            total_value += price * quantity
    return total_value

def generate_pdf_report(portfolio):
    # Generate file name with current date
    file_name = f"portfolio_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=letter)
    data = []

    # Add header row
    data.append(["Coin", "Price", "1h Change", "24h Change", "7d Change", "Quantity", "Value"])

    for coin, quantity in portfolio.items():
        price, change_1h, change_24h, change_7d = fetch_data(coin)
        
        if price is not None and all(change is not None for change in [change_1h, change_24h, change_7d]):
            coin_value = price * quantity
            data.append([coin, f"${price:.2f}", f"{change_1h:.2f}%", f"{change_24h:.2f}%", f"{change_7d:.2f}%", str(quantity), f"${coin_value:.2f}"])
        else:
            price = price if price is not None else "Price not available"
            change_1h = f"{change_1h:.2f}%" if change_1h is not None else "N/A"
            change_24h = f"{change_24h:.2f}%" if change_24h is not None else "N/A"
            change_7d = f"{change_7d:.2f}%" if change_7d is not None else "N/A"
            coin_value = price * quantity if price is not None else ""
            data.append([coin, price, change_1h, change_24h, change_7d, str(quantity), coin_value])

    # Add total portfolio value
    total_value = calculate_portfolio_value(portfolio)
    data.append(["", "", "", "", "", "Total Portfolio Value", f"${total_value:.2f}"])

    # Add date
    data.append(["", "", "", "", "", "Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    # Create table
    table = Table(data)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                               ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

    # Add table to document
    doc.build([table])

def display_portfolio(portfolio):
    def sort_column(tree, col, reverse):
        l = [(float(tree.set(k, col)), k) for k in tree.get_children('')]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            tree.move(k, '', index)

        tree.heading(col, command=lambda: sort_column(tree, col, not reverse))

    root = tk.Tk()
    root.title("Portfolio Display")

    title_label = tk.Label(root, text="Coingecko Portfolio", font=("Helvetica", 16, "bold"))
    title_label.pack()

    total_value_label = tk.Label(root, text=f"Total Portfolio Value: ${calculate_portfolio_value(portfolio):.2f}", font=("Helvetica", 12))
    total_value_label.pack()

    tree = ttk.Treeview(root, columns=("Coin", "Price", "1h Change", "24h Change", "7d Change", "Quantity", "Value"))
    tree.heading("#0", text="Coin", command=lambda: sort_column(tree, "#0", False))
    tree.heading("#1", text="Price", command=lambda: sort_column(tree, "#1", False))
    tree.heading("#2", text="1h Change", command=lambda: sort_column(tree, "#2", False))
    tree.heading("#3", text="24h Change", command=lambda: sort_column(tree, "#3", False))
    tree.heading("#4", text="7d Change", command=lambda: sort_column(tree, "#4", False))
    tree.heading("#5", text="Quantity", command=lambda: sort_column(tree, "#5", False))
    tree.heading("#6", text="Value", command=lambda: sort_column(tree, "#6", False))

    for coin, quantity in portfolio.items():
        price, change_1h, change_24h, change_7d = fetch_data(coin)
        
        if price is not None and all(change is not None for change in [change_1h, change_24h, change_7d]):
            coin_value = price * quantity
            tree.insert("", "end", text=coin, values=(price, change_1h, change_24h, change_7d, quantity, coin_value))
        else:
            price = price if price is not None else "Price not available"
            change_1h = f"{change_1h:.2f}%" if change_1h is not None else "N/A"
            change_24h = f"{change_24h:.2f}%" if change_24h is not None else "N/A"
            change_7d = f"{change_7d:.2f}%" if change_7d is not None else "N/A"
            coin_value = price * quantity if price is not None else ""
            tree.insert("", "end", text=coin, values=(price, change_1h, change_24h, change_7d, quantity, coin_value))

    tree.pack(expand=True, fill="both")
    root.mainloop()


def main():
    # Check if .env file exists
    if not os.path.isfile('.env'):
        print("Error: The .env file does not exist.")
        return
    
    # Check if portfolio.json file exists
    portfolio_file = "portfolio.json"
    if not os.path.isfile(portfolio_file):
        print("Error: The portfolio.json file does not exist.")
        return

    while True:
        # Ping CoinGecko API to check response
        url = "https://api.coingecko.com/api/v3/ping"
        headers = {"x-cg-demo-api-key": os.getenv("API_KEY")}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Failed to connect to CoinGecko API. Please try again later.")
            break

        with open(portfolio_file) as f:
            portfolio = json.load(f)
        
        print("\n-----------------------------")
        print("  Coingecko Portfolio")
        print("-----------------------------\n")

        print("1. Refresh Portfolio Data")
        print("2. Generate PDF Report")
        print("3. Display Portfolio (GUI)")
        print("4. Exit")

        choice = input("Enter your choice: ")
        if choice == '1':
            # Clear cached data
            global cached_data
            cached_data = {}
            for coin, quantity in portfolio.items():
                price, _, _, _ = fetch_data(coin)
                if price is not None:
                    coin_value = price * quantity
                    print(f"{coin}: {quantity} coins - ${coin_value:.2f} (Price: ${price:.2f})")
                else:
                    print(f"{coin}: {quantity} coins - Price not available")

            total_value = calculate_portfolio_value(portfolio)
            print(f"\nTotal Portfolio Value: ${total_value:.2f}\n")
            print("Portfolio data refreshed.")
        elif choice == '2':
            generate_pdf_report(portfolio)
            print("PDF report generated successfully.")
        elif choice == '3':
            display_portfolio(portfolio)
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter a valid option.")

if __name__ == "__main__":
    main()
