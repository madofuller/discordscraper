"""Database setup script."""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import yaml

from db.service import DatabaseService
from db.models import Base

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.yaml with environment variable substitution."""
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    
    with open(config_path, 'r') as f:
        config_str = f.read()
        
    # Replace environment variables
    for key, value in os.environ.items():
        config_str = config_str.replace(f'${{{key}}}', value)
    
    return yaml.safe_load(config_str)


def load_subnets():
    """Load subnet configurations."""
    subnets_path = Path(__file__).parent.parent / 'config' / 'subnets.yaml'
    
    with open(subnets_path, 'r') as f:
        data = yaml.safe_load(f)
    
    return data.get('subnets', [])


def setup_database():
    """Setup database tables and initial data."""
    try:
        # Load config
        config = load_config()
        db_config = config['database']
        
        # Build connection string
        connection_string = (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        # Initialize database service
        logger.info("Initializing database service...")
        db_service = DatabaseService(
            connection_string=connection_string,
            pool_size=db_config.get('pool_size', 5),
            max_overflow=db_config.get('max_overflow', 10)
        )
        
        # Create tables
        logger.info("Creating database tables...")
        db_service.create_tables()
        
        # Upsert server first
        logger.info("Setting up server...")
        server_id = int(config['discord']['server_id'])
        db_service.upsert_server(server_id=server_id, name="Bittensor Discord")
        
        # Load and insert subnets
        logger.info("Loading subnet configurations...")
        subnets = load_subnets()
        
        if subnets:
            for subnet_config in subnets:
                name = subnet_config['name']
                description = subnet_config.get('description')
                tags = subnet_config.get('tags', [])
                channel_id = int(subnet_config['channel_id'])
                
                # Upsert subnet
                db_service.upsert_subnet(name=name, description=description, tags=tags)
                logger.info(f"Upserted subnet: {name}")
                
                # Upsert channel (subnet linking can be done later if needed)
                db_service.upsert_channel(
                    channel_id=channel_id,
                    server_id=server_id,
                    name=name,
                    subnet_id=None  # Link manually later if needed
                )
                logger.info(f"Registered channel {channel_id} for subnet {name}")
        else:
            logger.warning("No subnets configured in subnets.yaml")
        
        logger.info("Database setup completed successfully!")
        
        # Close connections
        db_service.close()
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    setup_database()

