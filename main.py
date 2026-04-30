import snorte
from pathlib import Path
import csv
import smtplib
from email.message import EmailMessage
from datetime import datetime
import shutil
from logger import get_logger
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_SENHA = os.getenv("EMAIL_SENHA")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO", "")
TELEFONE_TI = os.getenv("TELEFONE_TI", "")
lista_emails = [email.strip() for email in EMAIL_DESTINO.split(",") if email.strip()]


log = get_logger(__name__)

class ConexaoBD:
    
    def __init__(self):
        try:
            self.conexao = snorte.Snorte()
            log.info("Conexão com o banco inicializada!")
        except Exception:
            self.conexao = None
            log.exception(f"Erro ao inicializar conexão.")

    def verifica_conexao(self) -> bool:
        if self.conexao and self.conexao.connection:
            log.info("Sucesso na conexão!")
            return True
        else:
            log.error("Erro ao conectar!")
            return False

    def fechar_conexao(self):
        if not self.conexao:
            return
        
        try:
            if self.conexao.cursor:
                self.conexao.cursor.close()
            if self.conexao.connection:
                self.conexao.connection.close()
            log.info("Conexão com o banco encerrada!")
        except Exception as e:
            log.warning(f"Erro inesperado ao fechar a conexão: {e}", exc_info=True)

class CarregarQueries():

    def __init__(self, diretorio_consultas: str = "queries"):
        self.base_path = Path(__file__).parent
        self.queries_path = self.base_path / diretorio_consultas
        self.queries = {}

        self.carregar_queries()

    def carregar_queries(self):
        if not self.queries_path.exists():
            log.error(f"Pasta de queries não encontrada: {self.queries_path}")
            raise FileNotFoundError()
        
        for arquivo in self.queries_path.glob("*.txt"):
            nome_query = arquivo.stem
            self.queries[nome_query] = arquivo.read_text(encoding="utf-8")
            log.info(f"Query carregada: {nome_query}")
    
    def get(self, nome: str) -> str:
        try:
            return self.queries[nome]
        except KeyError:
            raise KeyError(f"Query '{nome}' não encontrada!")
        
    def listar_queries(self):
        return list(self.queries.keys())
    
class ExecutarQueries():
    def __init__(self, conexao: ConexaoBD, queires: CarregarQueries, diretorio_resultados: str = "results"):
        self.conexao = conexao
        self.queries = queires
        self.base_path = Path(__file__).parent
        self.results_path = self.base_path / diretorio_resultados

        self.results_path.mkdir(exist_ok=True)

        self._limpar_resultados()

    def executar_queries(self):
        if not self.conexao.verifica_conexao():
            raise ConnectionError("Não há conexão com o banco!")
        
        cursor = self.conexao.conexao.cursor

        for nome_query in self.queries.listar_queries():
            log.info(f"Executando query: {nome_query}")

            try:
                sql = self.queries.get(nome_query)
                cursor.execute(sql)

                colunas = [desc[0] for desc in cursor.description]
                linhas = cursor.fetchall()

                self._salvar_csv(nome_query, colunas, linhas)
            except Exception:
                log.exception(f"Erro ao executar query: {nome_query}")
    
    def _salvar_csv(self, nome_query, colunas, linhas):
        arquivo_csv = self.results_path / f"{nome_query}.csv"

        with open(arquivo_csv, mode='w', newline="", encoding="utf-8") as arquivo:
            writer = csv.writer(arquivo, delimiter=";")
            writer.writerow(colunas)
            writer.writerows(linhas)
        
        log.info(f"Arquivo gerado: {arquivo_csv}")

    def _limpar_resultados(self):
        arquivos = list(self.results_path.glob("*.csv"))
        for arquivo in arquivos:
            arquivo.unlink()
        log.info("Arquivos antigos removidos da pasta results.")

class EnviarEmail():

    def __init__(
        self, 
        smtp_server: str,
        smtp_port: int,
        email_remetente: str,
        senha: str,
        emails_destinatarios: list[str]
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_remetente = email_remetente
        self.senha = senha
        self.emails_destinatarios = emails_destinatarios

    def enviar_email(self, pasta_results: Path):
        arquivos = list(pasta_results.glob("*.csv"))

        if not arquivos:
            log.warning("Nenhum arquivo CSV para envio.")
            return False
        
        log.info(f"Enviando email com {len(arquivos)} anexos.")

        msg = EmailMessage()
        msg["From"] = self.email_remetente
        msg["To"] = ", ".join(self.emails_destinatarios)
        msg["Subject"] = "Análise Comercial"
        msg.set_content(
            f"Relatório Diário - Criado em {datetime.now().strftime('%d-%m-%Y')} \n\nEsse email foi enviado automaticamente. Favor não responder. Em caso de dúvida, contatar a\n\nEquipe TI Supernorte - {TELEFONE_TI}\n\n"
        )
        
        for arquivo in arquivos:
            msg.add_attachment(
                arquivo.read_bytes(),
                maintype="text",
                subtype="csv",
                filename=arquivo.name
            )

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
               server.starttls()
               server.login(self.email_remetente, self.senha)
               server.send_message(msg)

            log.info("Email enviado com sucesso.")
            return True
        except Exception:
            log.exception(f"Erro ao enviar email.")
            return False

if __name__ == "__main__":

    inicio = datetime.now()
    log.info("===== INÍCIO DA EXECUÇÃO =====")

    try:
        conexao = ConexaoBD()
        queries = CarregarQueries()

        executor = ExecutarQueries(conexao, queries)
        executor.executar_queries()

        conexao.fechar_conexao()

        pasta_resultados = Path(__file__).parent / "results"

        email = EnviarEmail(
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT,
            email_remetente=EMAIL_REMETENTE,
            senha=EMAIL_SENHA,
            emails_destinatarios=lista_emails
        )

        enviado = email.enviar_email(pasta_resultados)

        if not enviado:
            log.warning("Email não enviado. Arquivos não foram encontrados.")
    except Exception:
        log.exception("Erro fatal durante a execução do processo!!")
    finally:
        fim = datetime.now()
        log.info(f"Tempo total de execução: {fim - inicio}")
        log.info("===== THAT'S ALL, FOLKS =====")