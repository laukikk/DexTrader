import logging

def configure_logging():
    # Create a main logger for the project
    main_logger = logging.getLogger('TradingBot')
    main_logger.setLevel(logging.DEBUG)  # Set the main logger's level to the lowest level you want to capture

    # Create separate handlers for different log files
    detailed_handler = logging.FileHandler('logs/detailed.log')
    debug_handler = logging.FileHandler('logs/debug.log')
    trade_handler = logging.FileHandler('logs/trade.log')
    error_handler = logging.FileHandler('logs/error.log')

    # Create formatters for the handlers
    formatter = logging.Formatter('[%(asctime)s] - %(name)s - %(levelname)s - %(message)s')

    # Assign formatters to handlers
    detailed_handler.setFormatter(formatter)
    debug_handler.setFormatter(formatter)
    trade_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # Set the appropriate levels for each handler
    detailed_handler.setLevel(logging.INFO)  # Captures INFO and above
    debug_handler.setLevel(logging.DEBUG)    # Captures DEBUG and above
    trade_handler.setLevel(logging.INFO)     # Captures INFO and above
    error_handler.setLevel(logging.ERROR)    # Captures ERROR and above

    # Add handlers to the main logger
    main_logger.addHandler(detailed_handler)
    main_logger.addHandler(debug_handler)
    main_logger.addHandler(trade_handler)
    main_logger.addHandler(error_handler)

    return main_logger