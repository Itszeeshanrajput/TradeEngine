import json
import time
import logging
from trader import Trader

# --- Main Setup ---
# This sets up logging to a file named 'trade_bot.log'.
logging.basicConfig(filename='trade_bot.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Main function to run the trading bot.
    It loads configurations and runs a trading session for each enabled account.
    """
    logging.info("=============================================")
    logging.info("Initializing Trading Bot...")

    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.error("Configuration file 'config.json' not found. Exiting.")
        return
    except json.JSONDecodeError:
        logging.error("Error decoding 'config.json'. Please check its format. Exiting.")
        return

    global_settings = config.get("global_settings", {})
    sleep_interval = global_settings.get("sleep_seconds", 300)

    while True:
        logging.info("Starting new trading cycle...")
        for account_config in config.get("accounts", []):
            if account_config.get("enabled", False):
                trader = Trader(account_config, global_settings)
                try:
                    trader.run_session()
                except Exception as e:
                    logging.error(f"A critical error occurred in trader for account {account_config['login']}: {e}")
            else:
                logging.info(f"Account {account_config.get('name', 'N/A')} is disabled. Skipping.")

        logging.info(f"Trading cycle complete. Sleeping for {sleep_interval} seconds.")
        time.sleep(sleep_interval)

if __name__ == "__main__":
    main()