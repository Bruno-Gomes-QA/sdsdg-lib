# SDSDG - Simplificando a Geração de Dados Sintéticos Orientados por Semântica

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pytest](https://img.shields.io/badge/pytest-%23ffffff.svg?style=for-the-badge&logo=pytest&logoColor=2f9fe3)
![ChatGPT](https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white)
![PyPi](https://img.shields.io/badge/pypi-%23ececec.svg?style=for-the-badge&logo=pypi&logoColor=1f73b7)

## 📌 O que é o SDSDG?

SDSDG é uma biblioteca poderosa e intuitiva para facilitar a geração de dados sintéticos com base na estrutura do banco de dados do usuário. Ideal para desenvolvedores, cientistas de dados e equipes de QA que precisam criar dados consistentes, seguros e prontos para uso em testes ou protótipos.

## ✨ Principais Funcionalidades

### 📊 Integração com Múltiplos Bancos de Dados

Gerencie conexões com bancos SQL como MySQL, PostgreSQL, SQLite, entre outros, em poucos passos.

### 🛠️ Geração de Modelos Automática
Use o sqlacodegen para traduzir a estrutura do banco em modelos Python prontos para uso com SQLAlchemy.

### 🤖 Assistente Semântico Alimentado por LLMs
Converse com um modelo avançado para gerar dados com base em prompts em linguagem natural, mantendo a consistência das relações e constraints do banco.

### ⚙️ Configuração e Uso Simplificados
Configure múltiplas conexões e gere dados de forma rápida com uma interface intuitiva.

### 🔒 Dados Seguros e Anonimizados
Gera dados que seguem as melhores práticas de segurança e anonimização, atendendo a normas como LGPD e GDPR.

### 🚀 Como pode te ajudar?
- Testes Automatizados: Gere cenários realistas com dados consistentes para validar a aplicação sem acessar dados reais.
- Desenvolvimento de Prototótipos: Popule rapidamente bancos de dados de desenvolvimento ou sandbox.
- Treinamento de Modelos de IA: Crie dados sintéticos com características específicas para treinar seus modelos.
- Análise de Dados: Simule cenários completos sem interferir no ambiente de produção.

### 🛠️ Como começar?
Siga estas etapas simples para utilizar a biblioteca:

- Instalação
```bash
pip install sdsdg-lib
```

- Configuração

Defina as configurações de conexão com seus bancos de dados:

```python
from sdsdg_lib import DatabaseConnectionManager, Generators

configs = [
    {
        'name': 'main_db',
        'dialect': 'mysql+pymysql',
        'username': 'seu_usuario',
        'password': 'sua_senha',
        'host': 'localhost',
        'port': 3306,
        'database': 'meu_banco',
    }
]

manager = DatabaseConnectionManager(configs)
```

- Geração de Dados

Conecte-se à LLM para gerar dados sintéticos com base em prompts:

```python
generator = Generators(manager, OPENAI_API_KEY="sua_chave_aqui")
prompt = "Gere 50 registros de vendas relacionadas a pessoas com idade acima de 30 anos."
response = generator.generate_data("main_db", prompt)
print(response)
```

- Geração de Modelos

Gere os modelos SQLAlchemy do banco de dados automaticamente:

```python
models_code = generator.generate_models("main_db", save_to_file=True)
print(models_code)
```

### 📚 Exemplos e Casos de Uso

- Gere 10 registros para cada tabela automaticamente:

```python
prompt = "Gere 10 registros para cada tabela do banco, respeitando as constraints."
print(generator.generate_data("main_db", prompt))
```

- Exporte os modelos SQLAlchemy para um arquivo específico:

```python
generator.generate_models("main_db", save_to_file=True)
```

### 📢 Dicas para Maximizar o Uso
- Use prompts claros e objetivos para gerar dados mais relevantes.
- Explore a flexibilidade de configuração para trabalhar com múltiplos bancos ao mesmo tempo.
- Combine os dados gerados com ferramentas de análise ou visualização para entender melhor os cenários simulados.


