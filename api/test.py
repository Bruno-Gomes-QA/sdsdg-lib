import os

from dotenv import load_dotenv

from SDSDG_Lib import DatabaseConnectionManager, Generators, DataHandler

load_dotenv()

configs = [
    {
        'name': 'main_db',
        'dialect': 'mysql+pymysql',
        'username': 'brunom',
        'password': 'toor',
        'host': 'localhost',
        'port': 3306,
        'database': 'meu_banco',
    }
]

db_m = DatabaseConnectionManager(configs)
generator = Generators(db_m, OPENAI_API_KEY=os.getenv('OPENAI_API_KEY'))

res = generator.generate_data(
    'main_db',
    'Gere 10 produtos em 4 departamentos distintos, esses dados devem ter relação com um supermercado',
)
print(res)
db_h = DataHandler(db_m.get_engine('main_db'))
db_h.insert(res)