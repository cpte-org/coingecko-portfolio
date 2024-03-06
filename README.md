# CoinGecko Portfolio Tracker

This is a work-in-progress (WIP) software for tracking your cryptocurrency portfolio using CoinGecko API.

## Introduction

This Python-based software allows you to manage your cryptocurrency portfolio with ease. You can add transactions, update prices, view portfolio values, import portfolios, and delete portfolios using this tool.

## Features

- **Create Portfolio:** Create a new portfolio with a custom name and currency.
- **Manage Portfolios:** Add transactions, update prices, view portfolio values, import portfolios from JSON files, and delete portfolios.
- **Currency Support:** Supports multiple currencies for portfolio tracking.
- **CoinGecko Integration:** Utilizes CoinGecko API for fetching real-time cryptocurrency data.

## Getting Started

To get started with the CoinGecko Portfolio Tracker, follow these steps:

1. **Clone Repository:**
   Clone this repository to your local machine:
   ```bash
   git clone https://github.com/cpte-org/coingecko-portfolio.git
   ```

2. **Install Dependencies:**
   Navigate to the project directory and install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Environment:**
   Create a `.env` file in the project directory and add your CoinGecko API key. You can use the provided `.env-example` file as a template.
   ```
   API_KEY=your_api_key_here
   ```

4. **Run the Application:**
   Run the application by executing the `main.py` file:
   ```bash
   python main.py
   ```

5. **Follow On-Screen Instructions:**
   Follow the on-screen instructions to create portfolios, add transactions, update prices, and perform other operations.

## Usage

Once the application is running, you'll be presented with a menu to create portfolios or manage existing ones. Follow the prompts to perform various portfolio management tasks.

## Example Portfolio File

An example portfolio file (`portfolio-example.json`) is provided in the repository. You can use this file to import sample portfolios into the application.

## Contributing

Contributions are welcome! If you have any suggestions, feature requests, or bug reports, please open an issue or submit a pull request on GitHub.

## License

This software is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**Disclaimer:** This software is provided "as is" without warranty of any kind. Use at your own risk.