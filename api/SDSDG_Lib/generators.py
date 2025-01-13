import os
import subprocess
import tiktoken

from openai import OpenAI

from .database import DatabaseConnectionManager


class Generators:
    def __init__(
        self, manager: DatabaseConnectionManager, OPENAI_API_KEY: str
    ):
        """
        Inicializa os geradores de dados e define o gerenciador de conexões.

        Args:
            manager (DatabaseConnectionManager): Gerenciador de conexões com bancos de dados.
            OPENAI_API_KEY (str): Chave de autenticação da API da OpenAI.
        """
        self.manager = manager
        self.models_dir = 'SDSDG_Models'
        self.history = {}  # Armazena o histórico de prompts e respostas
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        

    def generate_data(
        self,
        db_name: str,
        prompt: str,
        model: str = 'gpt-3.5-turbo-16k',
        max_tokens: int = 16385,
        temp: float = 0.3,
    ):
        """
        Gera dados semânticos usando o modelo OpenAI com base em um prompt.

        Args:
            db_name (str): Nome do banco de dados associado à geração de dados.
            prompt (str): Mensagem enviada ao modelo para geração de dados.
            model (str): Modelo OpenAI a ser utilizado (default: 'gpt-3.5-turbo').
            max_tokens (int): Número máximo de tokens permitidos na resposta (default: 4096).
            temp (float): Grau de criatividade da resposta (default: 0.3).

        Returns:
            str: Resposta gerada pelo modelo OpenAI.

        Raises:
            ValueError: Se o banco de dados não for encontrado.
            RuntimeError: Se ocorrer um erro na comunicação com a API da OpenAI.
        """
        content = """
Você é um assistente especializado em geração de dados sintéticos. Sua tarefa é gerar resultados no formato JSON e seguir rigorosamente as regras abaixo:

1. Todas as respostas devem ser entregues **apenas no formato JSON**. Não inclua explicações, comentários ou qualquer outro conteúdo fora do JSON.

2. Os dados devem ser gerados de acordo com a **estrutura fornecida** (tabelas, colunas e relações).

3. Respeite as **relações** e **constraints** definidas entre as tabelas:
   - As foreign keys devem estar consistentes com as tabelas relacionadas.
   - Os valores gerados devem ser válidos em relação aos tipos de dados e restrições (e.g., NOT NULL, UNIQUE, DEFAULT, etc.).
   - Leve em consideração a coerência do contexto. Por exemplo, se um produto pertence a um departamento, não faz sentido gerar 10 produtos com 10 departamentos completamente distintos sem relação.

4. Se o prompt não especificar a quantidade de dados, você deve gerar **10 registros por tabela** por padrão, respeitando as relações entre as tabelas. Caso o usuário especifique um número, siga a solicitação.

5. **Formato Padrão do JSON**:
   - A estrutura deve seguir a ordem das dependências:
     1. Primeiro, os dados que possuem **constraints de foreign key**, que outras tabelas possam referenciar.
     2. Depois, os dados que dependem de outras tabelas.
   - Cada tabela deve ser representada como uma chave no JSON:
     ```json
     {
         "nome_da_tabela": {
             "atributos": ["coluna1", "coluna2", "coluna3"],
             "valores": [
                 [valor1, valor2, valor3],
                 [valor4, valor5, valor6]
             ]
         }
     }
     ```
   - Cada tabela deve ser gerada no mesmo padrão, mantendo consistência entre os dados.

6. Algumas solicitações podem não gerar resultados válidos (e.g., estruturas incompletas ou conflitantes). Nesse caso, retorne um JSON vazio no seguinte formato:
   ```json
   {}
7. Se o usuário fornecer dados iniciais ou exemplos no prompt, utilize-os como base para gerar dados similares. Certifique-se de que os dados gerados sejam consistentes
com os fornecidos e sigam as instruções passadas pelo usuário.

8. Segurança e Anonimização:

    - Dados sensíveis (e.g., nomes, CPFs, e-mails) devem ser anonimizados e consistentes. Por exemplo:
        - Gerar nomes fictícios.
        - Substituir CPFs por números válidos mas não reais.
        - Utilizar domínios genéricos para e-mails (e.g., usuario@example.com).
    Respeite as regras de segurança de dados, evitando gerar informações que possam violar leis de privacidade (como GDPR ou LGPD).

9. Contexto do Banco de Dados:

    - Use o contexto geral do banco para gerar dados coerentes. Por exemplo:
        - Produtos devem pertencer a categorias válidas.
        - Funcionários devem ser atribuídos a departamentos relevantes.
        - Ordens de compra devem referenciar clientes e produtos existentes.

10. O JSON gerado deve cobrir todas as tabelas mencionadas na solicitação. Se alguma tabela for omitida, ela não deve aparecer no resultado.

11. Certifique-se de que os dados gerados sejam plausíveis e representem cenários realistas, evitando valores que não façam sentido no mundo
real (e.g., preços negativos ou idades impossíveis).

12. Se o banco de dados não tiver entidades, retornar um JSON vazio.

13. Gere dados em pt-BR e mude apenas se o usuário solicitar.
"""
        if db_name not in self.manager.connections:
            raise ValueError(
                f"O banco de dados '{db_name}' não foi encontrado no gerenciador."
            )
        
        database_structure = self.generate_models(db_name)

        database_structure_tokens = self.count_tokens(database_structure, model)
        content_tokens = self.count_tokens(content, model)
        prompt_tokens = self.count_tokens(prompt, model)
        res_tokens = max_tokens - (database_structure_tokens + content_tokens + prompt_tokens) - 40 #Overhead

        if res_tokens < 1000:
            raise ValueError(
                f'Quantidade de tokens menor que o mínimo de 1000: tokens restantes = {res_tokens}'
            )
        try:
            # Envia o prompt para o modelo
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        'role': 'system',  # Prompt para o modelo seguir as regras e entregar a melhor resposta no formato adequado
                        'content': content,
                    },
                    {
                        'role': 'system',
                        'content': database_structure,
                    },  # Estrutura do banco de dados solicitado
                    {'role': 'user', 'content': prompt},  # Prompt do usuário
                ],
                max_tokens=res_tokens,
                temperature=temp,
            )

            # Extrai o resultado da resposta
            result = response.choices[0].message.content

            # Salva no histórico
            gen_key = f'gen{len(self.history) + 1}'
            self.history[gen_key] = {'prompt': prompt, 'result': result}

            return result

        except Exception as e:
            raise RuntimeError(f'Erro ao gerar dados: {str(e)}')

    def generate_models(self, db_name: str, save_to_file: bool = False):
        """
        Gera os modelos SQLAlchemy do banco de dados especificado.

        Args:
            db_name (str): Nome do banco de dados a ser utilizado.
            save_to_file (bool): Indica se o código gerado deve ser salvo em arquivo. Default é False.

        Returns:
            str: Código gerado pelo sqlacodegen.

        Raises:
            ValueError: Se o banco de dados não for encontrado.
            RuntimeError: Se ocorrer um erro ao gerar os modelos.
        """
        if db_name not in self.manager.connections:
            raise ValueError(
                f"O banco de dados '{db_name}' não foi encontrado no gerenciador."
            )

        db_config = self.manager.get_config_by_name(db_name)
        db_url = self.manager.build_connection_url(db_config)

        try:
            # Verifica se o sqlacodegen está instalado
            result = subprocess.run(
                ['sqlacodegen', '--help'], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise EnvironmentError('sqlacodegen não está instalado.')

            # Gera os modelos do banco
            result = subprocess.run(
                ['sqlacodegen', db_url],
                capture_output=True,
                text=True,
                check=True,
            )
            code = result.stdout  # Código gerado em memória

            # Salva em arquivo, se solicitado
            if save_to_file:
                os.makedirs(
                    self.models_dir, exist_ok=True
                )  # Garante que a pasta models exista
                output_path = (
                    f'{self.models_dir}/{db_name}.py'  # Nome do arquivo
                )
                with open(output_path, 'w') as f:
                    f.write(code)
                print(f'Modelos salvos em: {output_path}')

            return code

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Erro ao gerar models para '{db_name}': {e.stderr}"
            )
        except Exception as e:
            raise RuntimeError(f'Erro inesperado ao gerar models: {str(e)}')
    
    @staticmethod
    def count_tokens(msg: str, model: str = 'gpt-3.5-turbo-16k'):
        try:
            encoding = tiktoken.encoding_for_model(model) # Inicia o tiktoken
            return len(encoding.encode(msg))
        except Exception as e:
            raise RuntimeError(f'Erro inesperado contar tokens: {str(e)}')
