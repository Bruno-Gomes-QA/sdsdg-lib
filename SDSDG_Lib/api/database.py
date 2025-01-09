from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Dict, Union

class DatabaseConnectionManager:
    """
    Gerencia conexões com bancos de dados, permitindo suporte a múltiplas conexões no futuro.

    Attributes:
        connections (dict): Um dicionário contendo as conexões ativas.
    """

    def __init__(self, configs: List[Dict[str, Union[str, int]]]):
        """
        Inicializa o gerenciador de conexões com base nas configurações fornecidas.

        Args:
            configs (list): Uma lista de configurações para conexão com bancos de dados.
                Cada item deve conter as chaves `name`, `dialect`, `username`, `password`, `host`, `port`, `database`.

        Examples:
            configs = [
                {
                    "name": "main_db",
                    "dialect": "mysql",
                    "username": "root",
                    "password": "password",
                    "host": "localhost",
                    "port": 3306,
                    "database": "meu_banco"
                }
            ]
        """
        self.connections = {}
        for config in configs:
            self.add_connection(config)

    def add_connection(self, config: Dict[str, Union[str, int]]):
        """
        Adiciona uma nova conexão ao gerenciador.

        Args:
            config (dict): Configurações para a conexão com o banco de dados.
        """
        connection_string = (
            f"{config['dialect']}://{config['username']}:{config['password']}@"
            f"{config['host']}:{config['port']}/{config['database']}"
        )
        engine = create_engine(connection_string)
        Session = sessionmaker(bind=engine)
        self.connections[config['name']] = {
            "engine": engine,
            "session": Session
        }

    def get_session(self, name: str):
        """
        Retorna uma sessão para o banco de dados especificado.

        Args:
            name (str): Nome da conexão configurada.

        Returns:
            sqlalchemy.orm.session.Session: Uma sessão para o banco de dados especificado.
        """
        if name not in self.connections:
            raise ValueError(f"Conexão '{name}' não encontrada.")
        return self.connections[name]["session"]()

    def close_all_connections(self):
        """
        Fecha todas as conexões gerenciadas.
        """
        for name, conn in self.connections.items():
            conn["engine"].dispose()
        self.connections.clear()