# Crypto Portfolio Tracker

This Python script allows you to track the value of your cryptocurrency portfolio using the CoinGecko API. You can easily edit your portfolio and refresh its valuation within the script.

## Prerequisites

- Python 3.x installed
- Dependencies installed (see `requirements.txt`)
- API key from [CoinGecko](https://www.coingecko.com/en/api)

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/cpte-org/crypto-portfolio-tracker.git
    ```

2. Navigate to the project directory:

    ```bash
    cd crypto-portfolio-tracker
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file based on `.env-example` and add your CoinGecko API key.

5. Optionally, create a `portfolio.json` file based on `portfolio-example.json` with your cryptocurrency holdings.

## Usage

Run the script:

```bash
python portfolio.py
```

Follow the on-screen instructions to edit your portfolio, refresh its valuation, or exit the program.

## Example Files

- `.env-example`: Example environment file.
- `portfolio-example.json`: Example portfolio file.

## Contributing

Contributions are welcome! Feel free to submit pull requests or open issues for bug fixes, feature requests, or general improvements.
