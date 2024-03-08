import requests
import sqlite3
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import webbrowser
from sql_queries import CREATE_PORTFOLIOS_TABLE, CREATE_TRANSACTIONS_TABLE, CREATE_COINS_TABLE

load_dotenv()


class CoinGeckoPortfolioManager:
    def __init__(self, portfolio_id, name, currency='usd'):
        self.portfolio_id = portfolio_id
        self.name = name
        self.portfolio = {}
        self.currency = currency.lower()
        self.conn = sqlite3.connect('portfolio.db')
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute(CREATE_PORTFOLIOS_TABLE)
        self.cursor.execute(CREATE_TRANSACTIONS_TABLE)
        self.cursor.execute(CREATE_COINS_TABLE)
        self.conn.commit()

    def load_transactions(self):
        self.cursor.execute('''SELECT coin_id, amount, price_per_coin FROM transactions WHERE portfolio_id = ?''',
                            (self.portfolio_id,))
        transactions = self.cursor.fetchall()
        for coin_id, amount, price_per_coin in transactions:
            self.portfolio[coin_id] = {'amount': amount, 'price': price_per_coin}

    def add_transaction(self, coin_id, amount, price_per_coin, date, transaction_type='buy'):
        if transaction_type.lower() == 'sell':
            current_holding = self.portfolio.get(coin_id, {'amount': 0})['amount']
            if current_holding < abs(amount):
                print("Error: Insufficient holding to sell.")
                return
            amount = -abs(amount)

        self.cursor.execute('''SELECT coin_id FROM coins WHERE coin_id = ?''', (coin_id,))
        existing_coin = self.cursor.fetchone()

        if not existing_coin:
            self.cursor.execute('''INSERT INTO coins (coin_id) VALUES (?)''', (coin_id,))

        self.cursor.execute('''INSERT INTO transactions (portfolio_id, coin_id, amount, price_per_coin, date, transaction_type) 
                            VALUES (?, ?, ?, ?, ?, ?)''',
                            (self.portfolio_id, coin_id, amount, price_per_coin, date, transaction_type))
        self.conn.commit()
        print(
            f"Transaction added to {self.name}: {transaction_type} {amount} {coin_id} on {date} at price {price_per_coin} {self.currency}")

    def modify_transactions(self):
        print("\n===== Modify Transactions =====")
        self.load_transactions()
        coin_ids = list(self.portfolio.keys())
        if not coin_ids:
            print("No transactions available. Please add transactions first.")
            return

        print("Coin IDs in portfolio:", ", ".join(coin_ids))
        coin_id = input("Enter coin ID to modify transactions for: ").lower()
        if coin_id not in coin_ids:
            print("Invalid coin ID. Please try again.")
            return

        self.cursor.execute('''SELECT id, amount, price_per_coin, date FROM transactions 
                                WHERE portfolio_id = ? AND coin_id = ?''', (self.portfolio_id, coin_id))
        transactions = self.cursor.fetchall()
        if not transactions:
            print("No transactions found for this coin.")
            return

        print(f"Current transactions for {coin_id}:")
        for idx, transaction in enumerate(transactions, start=1):
            print(f"{idx}- {transaction}")

        while True:
            try:
                choice = int(input("Which transaction would you like to edit? (Enter 0 to cancel): "))
                if choice == 0:
                    print("Transaction modification canceled.")
                    return

                if 1 <= choice <= len(transactions):
                    transaction_id, amount, price_per_coin, date = transactions[choice - 1]
                    print("Transaction details:")
                    print(f"Amount: {amount}")
                    new_amount = float(input("Enter new amount: "))
                    new_price_per_coin = float(input(f"Enter new price per coin ({price_per_coin}): ") or price_per_coin)
                    new_date = input(f"Enter new date ({date}): ") or date
                    self.cursor.execute('''UPDATE transactions 
                                        SET amount = ?, price_per_coin = ?, date = ? 
                                        WHERE id = ?''',
                                        (new_amount, new_price_per_coin, new_date, transaction_id))
                    self.conn.commit()
                    print("Transaction edited successfully.")
                    break
                else:
                    print("Invalid transaction number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")

    def update_prices(self):
        self.load_transactions()
        for coin_id in self.portfolio.keys():
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
            response = requests.get(url)
            if response.status_code == 200:
                coin_data = response.json()
                last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cursor.execute(
                    '''INSERT OR REPLACE INTO coins (coin_id, coin_data, last_updated) VALUES (?, ?, ?)''',
                    (coin_id, json.dumps(coin_data), last_updated))
                self.conn.commit()
            else:
                headers = {"x-cg-demo-api-key": os.getenv("API_KEY")}
                response_with_key = requests.get(url, headers=headers)
                if response_with_key.status_code == 200:
                    coin_data = response_with_key.json()
                    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.cursor.execute(
                        '''INSERT OR REPLACE INTO coins (coin_id, coin_data, last_updated) VALUES (?, ?, ?)''',
                        (coin_id, json.dumps(coin_data), last_updated))
                    self.conn.commit()
                else:
                    print(f"Failed to update data for {coin_id}. Please try again later.")

    def get_portfolio_value(self):
        self.load_transactions()
        portfolio_data = {'coins': {}}

        for coin_id, coin_data in self.portfolio.items():
            amount = 0
            self.cursor.execute('''SELECT amount FROM transactions WHERE portfolio_id = ? AND coin_id = ?''',
                                (self.portfolio_id, coin_id))
            transactions = self.cursor.fetchall()
            for transaction in transactions:
                amount += transaction[0]

            self.cursor.execute(
                '''SELECT coin_data FROM coins WHERE coin_id = ? ORDER BY last_updated DESC LIMIT 1''', (coin_id,))
            coin_json = self.cursor.fetchone()
            if coin_json and coin_json[0]:
                coin_data = json.loads(coin_json[0])
                price = coin_data['market_data']['current_price'][self.currency]
                portfolio_data['coins'][coin_id] = {'amount': amount, 'price': price}

        return portfolio_data

    def delete_portfolio(self):
        self.cursor.execute('''UPDATE portfolios SET deleted = 1 WHERE id = ?''', (self.portfolio_id,))
        self.conn.commit()
        self.conn.close()


class CoinGeckoCLI:
    def __init__(self):
        self.portfolios = {}
        self.conn = sqlite3.connect('portfolio.db')
        self.cursor = self.conn.cursor()
        self.create_portfolio_table()
        self.load_portfolios()

    def load_portfolios(self):
        self.cursor.execute('''SELECT id, name, currency, deleted FROM portfolios WHERE deleted = 0''')
        portfolios = self.cursor.fetchall()
        for portfolio_id, name, currency, deleted in portfolios:
            if not deleted:
                self.create_portfolio_object(portfolio_id, name, currency)

    def create_portfolio_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS portfolios (
                                id INTEGER PRIMARY KEY,
                                name TEXT,
                                currency TEXT,
                                deleted INTEGER DEFAULT 0
                                )''')
        self.conn.commit()

    def create_portfolio_object(self, portfolio_id, name, currency):
        self.portfolios[portfolio_id] = CoinGeckoPortfolioManager(portfolio_id, name, currency)

    def menu(self):
        print("\n===== CoinGecko Portfolio Manager =====")
        print("1. Create Portfolio")
        print("2. Manage Portfolios")
        print("0. Exit")

    def manage_portfolios_menu(self):
        print("\n===== Manage Portfolios =====")
        print("1. Add Transaction")
        print("2. Update Prices")
        print("3. View Portfolio Value")
        print("4. Import Portfolio")
        print("5. Modify Transactions")
        print("6. Delete Portfolio")
        print("0. Back")

    def create_portfolio(self):
        name = input("Enter portfolio name: ")
        currency = input("Enter currency (default: usd): ").lower() or 'usd'
        self.cursor.execute('''INSERT INTO portfolios (name, currency) VALUES (?, ?)''', (name, currency))
        self.conn.commit()
        portfolio_id = self.cursor.lastrowid
        self.create_portfolio_object(portfolio_id, name, currency)
        print(f"Portfolio '{name}' created successfully.")

    def select_portfolio(self):
        print("\n===== Select Portfolio =====")
        portfolios = list(self.portfolios.values())
        if not portfolios:
            print("No portfolios available. Please create a portfolio first.")
            return None

        for idx, portfolio in enumerate(portfolios, start=1):
            print(f"{idx}. {portfolio.name}")
        choice = int(input("Enter portfolio number: "))
        if 1 <= choice <= len(portfolios):
            return portfolios[choice - 1]
        else:
            print("Invalid portfolio number. Please try again.")
            return None

    def add_transaction(self, portfolio):
        coin_id = input("Enter coin ID: ")
        amount = float(input("Enter amount: "))
        price_per_coin = float(input("Enter price per coin: "))
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        transaction_type = input("Enter transaction type (buy/sell): ").lower()
        portfolio.add_transaction(coin_id, amount, price_per_coin, date, transaction_type)

    def modify_transactions(self, portfolio):
        portfolio.modify_transactions()

    def update_prices(self, portfolio):
        portfolio.update_prices()
        print("Prices updated successfully.")

    def view_portfolio_value(self, portfolio, display_mode='cli'):
        portfolio_value = portfolio.get_portfolio_value()
        if display_mode == 'cli':
            print("Portfolio Value:")
            print(json.dumps(portfolio_value, indent=4))
        elif display_mode == 'web':
            with open("portfolio_template.html", "r") as template_file:
                template_content = template_file.read()
            template_content = template_content.replace("{{portfolio_value}}", json.dumps(portfolio_value))
            with open("portfolio_value.html", "w") as output_file:
                output_file.write(template_content)
            webbrowser.open_new_tab("portfolio_value.html")
            print("Portfolio value saved to portfolio_value.html and opened automatically.")
        else:
            print("Invalid display mode. Defaulting to CLI.")
            print("Portfolio Value:")
            print(json.dumps(portfolio_value, indent=4))

    def delete_portfolio(self, portfolio):
        portfolio.delete_portfolio()
        del self.portfolios[portfolio.portfolio_id]
        print(f"Portfolio '{portfolio.name}' deleted successfully.")

    def run(self):
        while True:
            self.menu()
            choice = input("Enter your choice: ")

            if choice == '1':
                self.create_portfolio()
            elif choice == '2':
                portfolio = self.select_portfolio()
                if portfolio:
                    while True:
                        self.manage_portfolios_menu()
                        choice = input("Enter your choice: ")

                        if choice == '1':
                            self.add_transaction(portfolio)
                        elif choice == '2':
                            self.update_prices(portfolio)
                        elif choice == '3':
                            display_mode = input("Choose display mode (cli/web): ")
                            self.view_portfolio_value(portfolio, display_mode)
                        elif choice == '4':
                            portfolio_json_path = input("Enter the path to the portfolio.json file: ")
                            portfolio_json_path = os.path.abspath(os.path.expanduser(portfolio_json_path))
                            try:
                                with open(portfolio_json_path, 'r') as f:
                                    portfolio_data = json.load(f)
                                    for coin_id, details in portfolio_data.items():
                                        amount = details['amount']
                                        price_per_coin = details['price_per_coin']
                                        date = details['date']
                                        transaction_type = details['transaction_type']
                                        portfolio.add_transaction(coin_id, amount, price_per_coin, date,
                                                                  transaction_type)
                                print("Portfolio imported successfully.")
                            except FileNotFoundError:
                                print("File not found. Please check the file path and try again.")
                            except json.JSONDecodeError:
                                print("Invalid JSON format in the portfolio file.")
                        elif choice == '5':
                            self.modify_transactions(portfolio)
                        elif choice == '6':
                            confirm = input("Are you sure you want to delete this portfolio? (yes/no): ")
                            if confirm.lower() == 'yes':
                                self.delete_portfolio(portfolio)
                                break
                        elif choice == '0':
                            break
                        else:
                            print("Invalid choice. Please try again.")
            elif choice == '0':
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    cli = CoinGeckoCLI()
    cli.run()
