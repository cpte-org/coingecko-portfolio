import requests
import json
import subprocess
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def fetch_price(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
    headers = {"x-cg-demo-api-key": os.getenv("API_KEY")}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data[coin]['usd']
    else:
        print(f"Failed to fetch price for {coin}.")
        return None

def calculate_portfolio_value(portfolio):
    total_value = 0
    for coin, quantity in portfolio.items():
        price = fetch_price(coin)
        if price is not None:
            total_value += price * quantity
    return total_value

def edit_portfolio(portfolio_file):
    print("\n-----------------------------")
    print("      Edit Portfolio")
    print("-----------------------------\n")
    print("Opening portfolio file with Nano...\n")

    # Open the portfolio file with Nano
    subprocess.run(["nano", portfolio_file])

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
        response = requests.get(url)
        if response.status_code != 200:
            print("Failed to connect to CoinGecko API. Please try again later.")
            break

        with open(portfolio_file) as f:
            portfolio = json.load(f)
        
        print("\n-----------------------------")
        print("  Current Portfolio Value")
        print("-----------------------------\n")
        
        for coin, quantity in portfolio.items():
            price = fetch_price(coin)
            if price is not None:
                coin_value = price * quantity
                print(f"{coin}: {quantity} coins - ${coin_value:.2f} (Price: ${price:.2f})")
            else:
                print(f"{coin}: {quantity} coins - Price not available")

        total_value = calculate_portfolio_value(portfolio)
        print(f"\nTotal Portfolio Value: ${total_value:.2f}\n")

        print("1. Edit Portfolio")
        print("2. Refresh Portfolio Valuation")
        print("3. Exit")

        choice = input("Enter your choice: ")
        if choice == '1':
            edit_portfolio(portfolio_file)
        elif choice == '2':
            pass  # For now, refreshing is done automatically after editing
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter a valid option.")

if __name__ == "__main__":
    main()
