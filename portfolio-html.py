from flask import Flask, jsonify, request
import requests
import json
from dotenv import load_dotenv
import os
import pickle
from datetime import datetime
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()


# Global variable for cached data
CACHE_FILE = "cached_data.dat"
PORTFOLIO_FILE = "portfolio.json"
cached_data = {}
portfolio_data = {}

# Variable to store the active portfolio ID
active_portfolio_id = None

# Initialize Flask app
app = Flask(__name__)


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


def generate_portfolio_report(portfolio_id, use_savings=True):
    if portfolio_id not in portfolio_data:
        return jsonify({"error": "Portfolio ID not found"}), 404

    portfolio = portfolio_data[portfolio_id]
    data = []

    for coin, quantity in portfolio.items():
        price, change_1h, change_24h, change_7d = fetch_data(coin, use_savings)
        if price is not None:
            coin_value = price * quantity
            data.append({
                "coin": coin,
                "quantity": quantity,
                "value": coin_value,
                "price": price,
                "change_24h": change_24h
            })
        else:
            data.append({
                "coin": coin,
                "quantity": quantity,
                "value": "Price not available",
                "price": None,
                "change_24h": None
            })

    total_value = calculate_portfolio_value(portfolio, use_savings)
    return jsonify({"portfolio": data, "total_value": total_value}), 200


def update_portfolio(portfolio_id, updated_portfolio):
    if portfolio_id not in portfolio_data:
        return jsonify({"error": "Portfolio ID not found"}), 404

    portfolio_data[portfolio_id] = updated_portfolio
    save_portfolio_data()
    return jsonify({"message": "Portfolio updated successfully"}), 200


@app.route('/portfolio/<portfolio_id>', methods=['GET'])
def get_portfolio(portfolio_id):
    use_savings = request.args.get('savings', 'true').lower() != 'false'
    return generate_portfolio_report(portfolio_id, use_savings)


@app.route('/portfolio/<portfolio_id>', methods=['POST'])
def update_portfolio_route(portfolio_id):
    data = request.json
    if not data:
        return jsonify({"error": "No data provided in request body"}), 400

    updated_portfolio = data.get("portfolio")
    if not updated_portfolio:
        return jsonify({"error": "No portfolio data provided"}), 400

    return update_portfolio(portfolio_id, updated_portfolio)


if __name__ == "__main__":
    CORS(app)
    app.run(debug=True)
