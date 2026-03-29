"""Module to run program"""
import argparse
from src import create_app
from src.config.config import DevelopmentConfig, TestingConfig, ProductionConfig


app = create_app(config_class=ProductionConfig)


def main(config_class):
    """Create the app using the selected configuration"""
    app = create_app(config_class=config_class)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run Flask app")
    parser.add_argument('--dev', action='store_true', help='Development Environment')
    parser.add_argument('--test', action='store_true', help='Testing Environment')
    parser.add_argument('--production', action='store_true', help='Production Environment')
    args = parser.parse_args()
    configClass = DevelopmentConfig

    # Determine the config class based on the arguments
    if args.production:
        configClass = ProductionConfig
    elif args.test:
        configClass = TestingConfig
    elif args.dev:
        configClass = DevelopmentConfig

    main(configClass)

    app.run()
