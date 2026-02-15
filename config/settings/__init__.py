import os
from dotenv import load_dotenv # type: ignore

# Load environment variables from .env file
load_dotenv()

# Determine environment (default to development)
environment = os.environ.get('DJANGO_ENV', 'development')

if environment == 'production':
    from .production import *
else:
    from .development import *   
