import yaml

from src.utils.logging_config import configure_logging
from src.data import binance_historic as data
from src.strategies.triple_supertrend import TripleSupertrendStrategy

logger = configure_logging()

def main(config):
    logger.info('Starting Trading Bot')
    print('GETTING HISTORIC DATA...')
    df = data.get_historic_data(symbol=config['trade_symbol'], 
                                interval=config['time_interval'], 
                                days=config['timeframe'])
    print('CALCULATING INDICATORS...')
    strategy = TripleSupertrendStrategy(df, config)
    print('INITIALIZING BACKTEST...')
    strategy.run()



if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    main(config)