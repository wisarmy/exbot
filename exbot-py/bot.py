import argparse
import logging
from config import load_config

from exchanges import exchange

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='exbot for python')
    parser.add_argument('-c', '--config', type=str, required=True, help='config file path')
    parser.add_argument('--symbol', type=str, required=True, help='The trading symbol to use')
    # add arg verbose
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose mode')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info('exbot start')

    logging.info(args.config)

    config = load_config(args.config)
    
    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()
    print(args)
    print(ex.id())
    print(ex.get_balance('USDT'))
    


