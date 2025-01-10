from SDSDG_Lib import DatabaseConnectionManager

configs = [
    {
        'name': 'main_db',
        'dialect': 'mysql+pymysql',
        'username': 'root',
        'password': 'password',
        'host': 'localhost',
        'port': 3306,
        'database': 'meu_banco',
    }
]

db_m = DatabaseConnectionManager(configs)
