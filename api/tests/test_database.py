from unittest.mock import MagicMock, patch

import pytest

from SDSDG_Lib import DatabaseConnectionManager


@pytest.fixture
def db_configs():
    return [
        {
            'name': 'test_db_1',
            'dialect': 'sqlite',
            'username': '',
            'password': '',
            'host': '',
            'port': '',
            'database': ':memory:',
        },
        {
            'name': 'test_db_2',
            'dialect': 'mysql+pymysql',
            'username': 'root',
            'password': 'toor',
            'host': 'localhost',
            'port': 3306,
            'database': 'test_db',
        },
    ]


def test_initialization_creates_connections(db_configs):
    """Testa se as conexões são inicializadas corretamente."""
    with patch(
        'SDSDG_Lib.DatabaseConnectionManager.generate_models'
    ) as mock_generate_models:
        mock_generate_models.return_value = (
            None  # Evita a execução real do sqlacodegen
        )
        manager = DatabaseConnectionManager(db_configs)
    print(len(db_configs))
    print(manager.connections)
    assert len(manager.connections) == 2
    assert 'test_db_1' in manager.connections
    assert 'test_db_2' in manager.connections


def test_add_connection(db_configs):
    """Testa a adição de uma nova conexão."""
    manager = DatabaseConnectionManager([])
    config = db_configs[0]

    with patch(
        'SDSDG_Lib.DatabaseConnectionManager.generate_models'
    ) as mock_generate_models:
        mock_generate_models.return_value = None
        manager.add_connection(config)

    assert len(manager.connections) == 1
    assert 'test_db_1' in manager.connections


def test_add_connection_missing_keys():
    """Testa se a exceção é levantada ao adicionar conexão com configuração incompleta."""
    manager = DatabaseConnectionManager([])

    incomplete_config = {
        'name': 'invalid_db',
        'dialect': 'sqlite',
    }  # Configuração incompleta

    with pytest.raises(
        ValueError,
        match='Configuração inválida, valores ausentes ou vazios: database',
    ):
        manager.add_connection(incomplete_config)


def test_get_session(db_configs):
    """Testa a recuperação de uma sessão válida."""
    with patch(
        'SDSDG_Lib.DatabaseConnectionManager.generate_models'
    ) as mock_generate_models:
        mock_generate_models.return_value = (
            None  # Evita a execução real do sqlacodegen
        )
        manager = DatabaseConnectionManager(db_configs)

    session = manager.get_session('test_db_1')
    assert session is not None


def test_close_all_connections(db_configs):
    """Testa se todas as conexões são fechadas corretamente."""
    with patch(
        'SDSDG_Lib.DatabaseConnectionManager.generate_models'
    ) as mock_generate_models:
        mock_generate_models.return_value = (
            None  # Evita a execução real do sqlacodegen
        )
        manager = DatabaseConnectionManager(db_configs)

    assert len(manager.connections) == 2
    manager.close_all_connections()
    assert len(manager.connections) == 0


def test_build_connection_url():
    """Testa se a URL de conexão é construída corretamente."""
    config = {
        'dialect': 'mysql',
        'username': 'user',
        'password': 'pass',
        'host': 'localhost',
        'port': 3306,
        'database': 'testdb',
    }
    expected_url = 'mysql://user:pass@localhost:3306/testdb'

    url = DatabaseConnectionManager.build_connection_url(config)
    assert url == expected_url
