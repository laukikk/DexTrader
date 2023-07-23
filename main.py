import yaml


from src.data import binance_historic as data
from src.strategies.triple_supertrend import TripleSupertrendStrategy


def main(config):
    df = data.get_historic_data(symbol=config['trade_symbol'], interval=config['time_interval'])
    strategy = TripleSupertrendStrategy(df, config)
    strategy.run()



if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    main(config)