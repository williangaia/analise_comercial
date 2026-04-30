# Análise Comercial — Automação de Relatórios Diários

Script de automação para extração de dados estratégicos do banco Oracle, geração de relatórios em CSV e envio automático por e-mail. Executado diariamente às 5h pelo Agendador de Tarefas do servidor de aplicações.

---

## 🖥️ Visão Geral

O sistema carrega consultas SQL de arquivos de texto, executa cada uma delas contra o banco de dados Oracle, exporta os resultados como arquivos CSV e os envia automaticamente por e-mail para os destinatários configurados.

---

## 🏗️ Arquitetura

O projeto segue o princípio de **responsabilidade única (SRP)**, com cada classe cuidando de apenas uma etapa do processo.

```
executar_relatorio.bat       ← Agendador de Tarefas chama este arquivo
    └── main.py              ← Orquestrador principal
          ├── logger.py      ← Módulo de logging centralizado
          ├── queries/       ← Consultas SQL em arquivos .txt
          ├── results/       ← CSVs gerados (limpos a cada execução)
          └── logs/          ← Logs diários de execução
```

### Classes e Responsabilidades

| Classe | Responsabilidade |
|---|---|
| `ConexaoBD` | Conexão e desconexão com o banco Oracle via `snorte` |
| `CarregarQueries` | Lê os arquivos `.txt` da pasta `queries/` para um dicionário `{nome: sql}` |
| `ExecutarQueries` | Limpa a pasta `results/`, executa cada query e salva o resultado como CSV |
| `EnviarEmail` | Monta o e-mail com os CSVs como anexo e realiza o envio via SMTP com TLS |
| `logger` (módulo) | Registra logs em arquivo diário (`app_DD-MM-YYYY.log`) e no console simultaneamente |

---

## 🔄 Fluxo de Execução

```
Agendador de Tarefas (05h)
    └── executar_relatorio.bat
          └── python main.py
                ├── 1. Conecta ao Oracle via ConexaoBD
                ├── 2. Carrega todas as queries da pasta queries/
                ├── 3. Limpa arquivos antigos de results/
                ├── 4. Executa cada query → salva CSV em results/
                ├── 5. Encerra conexão com o banco
                └── 6. Envia e-mail com os CSVs anexados
```

---

## 🗂️ Estrutura de Arquivos

```
projeto/
├── main.py                    # Ponto de entrada e orquestrador
├── logger.py                  # Configuração centralizada de logs
├── executar_relatorio.bat     # Script de execução para o Agendador de Tarefas
├── .env                       # Variáveis de ambiente
├── .gitignore                 # Ignora .env, results/ e logs/
├── queries/                   # Consultas SQL em arquivos .txt
│   ├── AgendaFornecedores.txt
│   ├── Estoque.txt
│   ├── ProdutoCategoria.txt
│   ├── ProdutoEmpresa.txt
│   └── Vendas.txt
├── results/                   # CSVs gerados (limpos a cada execução)
└── logs/                      # Logs diários: app_DD-MM-YYYY.log
```

---

## ⚙️ Configuração

### 1. Instalar dependências

```bash
pip install python-dotenv
```

> **Nota:** `snorte` é uma biblioteca interna de conexão com Oracle.

### 2. Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha com os dados reais:

```bash
cp .env.example .env
```

Edite o arquivo `.env`:

```env
SMTP_SERVER=smtp.exemplo.com
SMTP_PORT=666
EMAIL_REMETENTE=remetente@empresa.com
EMAIL_SENHA=sua_senha_aqui
EMAIL_DESTINO=destinatario1@email.com,destinatario2@email.com
TELEFONE_TI = 4002-8922
```

### 3. Adicionar consultas SQL

Para incluir um novo relatório, basta salvar a consulta SQL como um arquivo `.txt` na pasta `queries/`. O nome do arquivo se torna o nome do CSV gerado.

**Exemplo:** `queries/NovaConsulta.txt` → gera `results/NovaConsulta.csv`

---

## 🚀 Execução Manual

```bash
python main.py
```

---

## 🖥️ Configuração no Servidor (Agendador de Tarefas)

O arquivo `executar_relatorio.bat` é registrado no **Agendador de Tarefas do Windows** para execução diária.

| Configuração | Valor |
|---|---|
| Arquivo executado | `executar_relatorio.bat` |
| Frequência | Diária |
| Horário | 05h00 |
| Diretório no servidor | `D:\pasta_do_BAT` |

---

## 📋 Queries Disponíveis

| Arquivo | Conteúdo |
|---|---|
| `Estoque.txt` | Posição atual de estoque por produto/empresa ⭐ |
| `Vendas.txt` | Dados de vendas consolidados ⭐ |
| `AgendaFornecedores.txt` | Agenda de fornecedores |
| `ProdutoCategoria.txt` | Produtos por categoria |
| `ProdutoEmpresa.txt` | Produtos por empresa/filial |

> ⭐ Consultas prioritárias conforme definição do solicitante.

---

## 📊 Logs

Os logs são gravados diariamente em `logs/app_DD-MM-YYYY.log` com o seguinte formato:

```
2026-04-30 05:00:01 | INFO  | __main__ | ===== INÍCIO DA EXECUÇÃO =====
2026-04-30 05:00:02 | INFO  | __main__ | Conexão com o banco inicializada!
2026-04-30 05:00:02 | INFO  | __main__ | Query carregada: Estoque
2026-04-30 05:00:05 | INFO  | __main__ | Arquivo gerado: results/Estoque.csv
2026-04-30 05:00:08 | INFO  | __main__ | Email enviado com sucesso.
2026-04-30 05:00:08 | INFO  | __main__ | Tempo total de execução: 0:00:06.412
2026-04-30 05:00:08 | INFO  | __main__ | ===== THAT'S ALL, FOLKS =====
```

---

## 🔒 Segurança

- Todas as credenciais (SMTP, e-mail, senha) são carregadas via **variáveis de ambiente** com `python-dotenv`
- O arquivo `.env` está listado no `.gitignore` e **nunca deve ser versionado**
---

## 💡 Decisões Técnicas

- **Design orientado a extensibilidade**: adicionar uma nova query não requer alteração de código — apenas um novo `.txt` na pasta `queries/`
- **Limpeza automática**: os CSVs da execução anterior são removidos antes de gerar os novos, evitando acúmulo de dados desatualizados
- **Logs com data no nome**: facilita auditoria no dia de falha
- **Bloco `finally`**: garante registro do tempo de execução mesmo em caso de erro fatal

---

## 👤 Autor

**Willian Gaia**  
Desenvolvedor Python | Analista de TI  
Tucuruí, Pará — Brasil
