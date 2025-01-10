import os
import subprocess
from typing import Dict, List, Union

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker


class DatabaseConnectionManager:
    """
    Esta classe gerencia conexões com múltiplos bancos de dados, suporta diferentes dialetos, gera models automaticamente para cada conexão ativa e facilita operações.

    Attributes:
        connections (dict):
            Dicionário contendo as conexões ativas.
            A chave é o nome da conexão e o valor é outro dicionário com o engine SQLAlchemy e a factory de sessões.

        models_dir (str):
            Caminho para a pasta onde os arquivos de models gerados serão salvos.
            O padrão é "models", criado automaticamente na inicialização da classe.

    Examples:
        >>> from SDSDG_Lib.database_manager import DatabaseConnectionManager

        ### Configurações de conexões
        >>> configs = [
                {
                    "name": "main_db",
                    "dialect": "mysql",
                    "username": "root",
                    "password": "password",
                    "host": "localhost",
                    "port": 3306,
                    "database": "meu_banco"
                },
                {
                    "name": "analytics_db",
                    "dialect": "postgresql",
                    "username": "admin",
                    "password": "admin123",
                    "host": "analytics.server.com",
                    "port": 5432,
                    "database": "analytics"
                }
            ]

        ### Cria o gerenciador de conexões
            >>> db_manager = DatabaseConnectionManager(configs)

        ### Obtém uma sessão para uma das conexões
            >>> session = db_manager.get_session("main_db")
    """

    def __init__(self, configs: List[Dict[str, Union[str, int]]]):
        """
        Inicializa o gerenciador de conexões com base nas configurações fornecidas.

        Args:
            configs (list): Uma lista de configurações para conexão com bancos de dados.
        """
        self.connections = {}
        self.models_dir = 'models'
        os.makedirs(
            self.models_dir, exist_ok=True
        )  # Garante que a pasta models exista
        for config in configs:
            try:
                self.add_connection(config)
            except Exception as e:
                print(
                    f"Erro ao adicionar conexão {config.get('name', '<sem_nome>')}: {e}"
                )

    def add_connection(self, config: Dict[str, Union[str, int]]):
        """
        Adiciona uma nova conexão ao gerenciador e gera os modelos correspondentes.

        Args:
            config (dict): Configurações para a conexão com o banco de dados.

        Raises:
            ValueError: Se o dicionário de configuração estiver incompleto.
        """
        required_keys = [
            'name',
            'dialect',
            'username',
            'password',
            'host',
            'port',
            'database',
        ]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(
                f"Configuração incompleta, chaves ausentes: {', '.join(missing_keys)}"
            )

        try:
            connection_string = self.build_connection_url(config)
            engine = create_engine(connection_string)
            Session = sessionmaker(bind=engine)
            self.connections[config['name']] = {
                'engine': engine,
                'session': Session,
            }

            # Gera os modelos para a conexão adicionada
            output_path = os.path.join(
                self.models_dir, f"{config['name']}_models.py"
            )
            self.generate_models(connection_string, output_path)
        except subprocess.SubprocessError as e:
            if 'Access denied' in str(e):
                raise PermissionError(
                    f'Acesso negado. '
                    'Verifique suas credenciais de autenticação.'
                ) from None
            raise ConnectionError(
                f'Não foi possível conectar ao banco de dados. '
                'Verifique as configurações de conexão e se o banco está acessível.'
            ) from None
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Erro ao gerar models para a conexão '{config['name']}': {e.stderr.decode().strip()}"
            ) from None
        except Exception as e:
            raise RuntimeError(
                f"Erro desconhecido ao criar conexão '{config['name']}': {e}"
            ) from None

    def get_session(self, name: str):
        """
        Retorna uma sessão para o banco de dados especificado.

        Args:
            name (str): Nome da conexão configurada.

        Returns:
            sqlalchemy.orm.session.Session: Uma sessão para o banco de dados especificado.

        Raises:
            ValueError: Se a conexão especificada não for encontrada.
        """
        if name not in self.connections:
            raise ValueError(f"Conexão '{name}' não encontrada.")
        try:
            return self.connections[name]['session']()
        except Exception as e:
            raise RuntimeError(
                f"Erro ao criar sessão para conexão '{name}': {e}"
            )

    def close_all_connections(self):
        """
        Fecha todas as conexões gerenciadas.
        """
        for name, conn in self.connections.items():
            try:
                conn['engine'].dispose()
            except Exception as e:
                print(f"Erro ao fechar conexão '{name}': {e}")
        self.connections.clear()

    @staticmethod
    def build_connection_url(config: Dict[str, Union[str, int]]) -> str:
        """
        Constrói uma URL de conexão a partir das configurações fornecidas.

        Args:
            config (dict): Configurações para a conexão com o banco de dados.

        Returns:
            str: URL de conexão no formato esperado por SQLAlchemy.

        Raises:
            ValueError: Se o dicionário de configuração estiver incompleto.
        """
        required_keys = [
            'dialect',
            'username',
            'password',
            'host',
            'port',
            'database',
        ]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(
                f"Configuração incompleta, chaves ausentes: {', '.join(missing_keys)}"
            )

        return (
            f"{config['dialect']}://{config['username']}:{config['password']}@"
            f"{config['host']}:{config['port']}/{config['database']}"
        )

    def generate_models(self, db_url: str, output_path: str):
        """
        Gera os modelos de tabelas do banco de dados utilizando o sqlacodegen.

        Args:
            db_url (str): URL de conexão ao banco de dados.
            output_path (str): Caminho para o arquivo onde os modelos gerados serão salvos.

        Raises:
            EnvironmentError: Caso o sqlacodegen não esteja instalado no ambiente.
            subprocess.CalledProcessError: Caso ocorra algum erro durante a execução do sqlacodegen.
            ValueError: Caso o output_path seja inválido ou não seja possível salvar o arquivo.
        """
        try:
            # Verifica se o sqlacodegen está instalado
            result = subprocess.run(
                ['sqlacodegen', '--help'], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise EnvironmentError('sqlacodegen não está instalado.')

            # Executa o comando para gerar os modelos
            subprocess.run(
                ['sqlacodegen', db_url, '--outfile', output_path],
                check=True,
            )
            print(f'Modelos gerados com sucesso em: {output_path}')
        except subprocess.CalledProcessError as e:
            raise subprocess.CalledProcessError(
                e.returncode, e.cmd, output=e.output, stderr=e.stderr
            )
        except Exception as e:
            raise ValueError(f'Erro ao gerar modelos: {e}')
