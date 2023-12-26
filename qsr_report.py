import psycopg2
from yourmarket_db_config import DB_CONFIG





def main():
    # Chrome setup and login code...

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    all_data =