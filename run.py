import argparse
import sys
import yaml
import os
import logging
from app.webapp import app, word_service
from app.word_service import WordService
from app.theme_service import ThemeService
from gunicorn.app.base import BaseApplication

def parse_args():
    parser = argparse.ArgumentParser(description='Word Generator Web Application')
    parser.add_argument('--init', action='store_true', help='Initialize database from words.txt')
    parser.add_argument('--dbname', help='SQLite database filename')
    parser.add_argument('--config', help='Path to configuration file')
    return parser.parse_args()

def load_default_config():
    """Load default configuration from config/default.yaml"""
    default_config_path = os.path.join('config', 'default.yaml')
    try:
        with open(default_config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.warning(f"Could not load default config: {e}")
        return None

def load_config(config_path):
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)

def ensure_data_directory():
    """Create data directory and sample words.txt if they don't exist"""
    data_dir = 'data'
    words_file = os.path.join(data_dir, 'words.txt')
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")
    
    if not os.path.exists(words_file) or os.path.getsize(words_file) == 0:
        sample_words = [
            "hello", "world", "python", "programming",
            "computer", "science", "database", "network",
            "system", "software", "developer", "engineer"
        ]
        with open(words_file, 'w') as f:
            f.write('\n'.join(sample_words))
        print(f"Created sample words file: {words_file}")

def initialize_database(word_service):
    print("Initializing database from words.txt...")
    try:
        ensure_data_directory()
        count = word_service.initialize_from_file('data/words.txt')
        print(f"Database initialization complete. Added {count} words.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

class GunicornApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.app = app
        self.options = options or {}
        super(GunicornApplication, self).__init__()

    def load(self):
        return self.app

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    args = parse_args()
    
    # Load default config first, then override with user config if provided
    config = None
    default_config = load_default_config()

    if args.config:
        user_config = load_config(args.config)
        if default_config:
            # Merge user config with default config
            config = default_config.copy()
            config.update(user_config)
        else:
            config = user_config
    else:
        config = default_config
    
    # Use config values or defaults
    if config and 'server' in config:
        host = config['server'].get('host', '127.0.0.1')
        port = config['server'].get('port', 5050)
    else:
        host = '127.0.0.1'
        port = 5050
    dbname = 'data/words.db'
    if config and 'database' in config:
        db_name = args.dbname or config['database'].get('path', 'data/words.db')
    else:
        db_name = args.dbname or 'data/words.db'
    
    word_service = WordService(db_name=db_name)
    
    if args.init:
        initialize_database(word_service)
        word_service.close()
        sys.exit(0)

    # Set the word service in the Flask app
    import app.webapp as webapp
    webapp.init_word_service(word_service)

    # Load themed word presets (in-memory) and wire them into the app.
    themes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'themes')
    webapp.init_theme_service(ThemeService(themes_dir=themes_dir))

    # Create Gunicorn application
    options = {
        'bind': f'{host}:{port}',  # Set host and port
        'workers': 4,              # Adjust based on the number of cores available
        'accesslog': '-',          # Log to stdout
        'errorlog': '-',           # Log to stderr
        'loglevel': 'info',        # Set log level to info for production
    }

    # Run the Gunicorn server
    GunicornApplication(app, options).run()

if __name__ == '__main__':
    main()
