import yaml

from src.utils.logging_config import configure_logging
from src.data import binance_historic as data
from src.strategies.triple_supertrend import TripleSupertrendStrategy

logger = configure_logging()

def main(config):
    logger.info('Starting Trading Bot')
    strategy = TripleSupertrendStrategy(config)
    strategy.run()



if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    print('STARTING BOT...')
    main(config)