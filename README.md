# Canvas Migrator

Ferramenta para migração seletiva de conteúdos entre disciplinas no Canvas LMS utilizando exclusivamente a API REST do Canvas.

O projeto foi desenvolvido para automatizar migrações em larga escala, permitindo importar conteúdo acadêmico, organizar módulos, gerar relatórios e retomar execuções interrompidas de forma segura.

## Principais Recursos

### Migração Seletiva de Conteúdo

Importação automatizada de:

- Páginas de conteúdo
- Arquivos (Attachments)
- Bancos de Questões

### Bancos de Questões Suportados

- Atv. Dissertativa
- Atv. Objetiva
- Atv. Objetiva 2
- Atv. Objetiva 3
- Atv. Objetiva 4
- Prova AO2
- Prova Substitutiva

### Organização Automática dos Módulos

Após a conclusão da migração o sistema:

- Reposiciona itens dentro dos módulos
- Publica conteúdos obrigatórios
- Despublica atividades configuradas
- Posiciona E-books, Materiais Adicionais, Podcasts e Vídeos
- Insere páginas de Tópicos nos módulos correspondentes
- Garante a presença das páginas "Aulas Gravadas" no módulo "Aulas"

### Recursos Operacionais

- Controle de execução por checkpoint
- Retomada automática após falhas
- Logs persistentes
- ETA (tempo estimado restante)
- Relatórios gerenciais
- Retry automático para requisições HTTP

---

# Arquitetura do Projeto

```text
canvas_migrator/

├── main.py
├── config.py
├── canvas_client.py
├── migration_service.py
├── module_service.py
├── report_service.py
├── checkpoint_service.py
├── logger.py
│
├── inputs/
│   └── oferta_disciplinas.xlsx
│
├── outputs/
│   ├── checkpoint.csv
│   ├── *_migration_processed.xlsx
│   ├── *_migration_failed.xlsx
│   └── *_migration_missing_bdq.xlsx
│
├── logs/
│   └── *.log
│
├── requirements.txt
├── .env
└── .gitignore
```

---

# Requisitos

- Python 3.12 ou superior
- Token de acesso à API do Canvas
- Permissão para executar Content Migrations

---

# Instalação

## 1. Criar ambiente virtual

### Windows

```bash
python -m venv venv
```

## 2. Ativar o ambiente virtual

```bash
venv\Scripts\activate
```

## 3. Instalar dependências

```bash
pip install -r requirements.txt
```

---

# Configuração

## Arquivo .env

Crie um arquivo `.env` na raiz do projeto:

```env
CANVAS_TOKEN=Bearer SEU_TOKEN_AQUI
```

---

## Arquivo config.py

Configure os parâmetros principais:

```python
MIGRATION_LIST = "inputs/oferta_disciplinas.xlsx"

SHEET_NAME = "Geral"

SKIP_ROWS = 0

LIMIT = 0
```

### Descrição

| Parâmetro | Descrição |
|------------|------------|
| MIGRATION_LIST | Caminho da planilha de entrada |
| SHEET_NAME | Nome da aba da planilha |
| SKIP_ROWS | Ignora linhas iniciais |
| LIMIT | Limita a quantidade de disciplinas processadas |

---

# Estrutura da Planilha

A planilha deve conter as seguintes colunas:

| Coluna | Descrição |
|----------|----------|
| DISCIPLINA | Nome da disciplina |
| IDENTIFICADOR | Identificador da disciplina no Canvas |
| LINK | Curso origem dos conteúdos |
| BDQ | Curso origem dos bancos de questões |

### Exemplo

| DISCIPLINA | IDENTIFICADOR | LINK | BDQ |
|------------|------------|------------|------------|
| Matemática | DPEAD20262.001 | ORIGEM001 | ORIGEM001 |

---

# Execução

Execute:

```bash
python main.py
```

---

# Fluxo de Processamento

Para cada disciplina o sistema executa:

```text
Localizar disciplina destino
        ↓
Iniciar migração seletiva
        ↓
Selecionar conteúdos válidos
        ↓
Enviar migração
        ↓
Aguardar conclusão
        ↓
Organizar módulos
        ↓
Inserir páginas de tópicos
        ↓
Inserir páginas de Aulas Gravadas
        ↓
Salvar checkpoint
        ↓
Atualizar ETA
        ↓
Próxima disciplina
```

---

# Checkpoint e Recuperação

Ao final do processamento de cada disciplina, o sistema grava o status no arquivo:

```text
outputs/checkpoint.csv
```

Exemplo:

```csv
identifier,status
DPEAD20262.001,SUCCESS
DPEAD20262.002,SUCCESS
DPEAD20262.003,FAILED
```

Caso a execução seja interrompida, basta executar novamente:

```bash
python main.py
```

As disciplinas já processadas serão ignoradas automaticamente.

---

# Logs

Cada execução gera um arquivo de log exclusivo.

Exemplo:

```text
logs/2026-08-21_11-42-13.log
```

Trecho de exemplo:

```text
2026-08-21 11:42:13 | INFO | Iniciando disciplina DPEAD20262.001
2026-08-21 11:43:06 | INFO | DPEAD20262.001 processada com sucesso
2026-08-21 11:43:06 | INFO | Progresso 1/1000 | ETA 08h 17m
```

---

# Relatórios Gerados

Ao término da execução são gerados os seguintes arquivos:

### Disciplinas Processadas

```text
outputs/*_migration_processed.xlsx
```

Contém:

- Curso
- Identificador
- Quantidade de páginas
- Quantidade de arquivos
- Quantidade de bancos migrados

### Disciplinas com Falha

```text
outputs/*_migration_failed.xlsx
```

Contém as disciplinas que apresentaram erro durante o processamento.

### Disciplinas sem Banco de Questões

```text
outputs/*_migration_missing_bdq.xlsx
```

Permite identificar disciplinas que não receberam bancos de questões.

---

# Segurança

O projeto utiliza exclusivamente a API REST do Canvas.

Não utiliza:

- Selenium
- BeautifulSoup
- Scraping HTML
- Cookies de navegador
- Tokens CSRF
- Automação de interface

Toda a comunicação ocorre através de endpoints oficiais da API.

---

# Boas Práticas

## Validação Inicial

Antes de processar grandes volumes, recomenda-se executar:

```python
LIMIT = 10
```

ou

```python
LIMIT = 20
```

para validação.

## Processamento em Larga Escala

O sistema foi preparado para trabalhar com grandes quantidades de disciplinas através de:

- Checkpoint automático
- Logs persistentes
- Retry automático de requisições
- Delay configurável entre requests
- ETA de acompanhamento
- Processamento disciplina a disciplina

---

# Histórico do Projeto

O projeto nasceu a partir de um notebook Jupyter utilizado para migração manual de disciplinas e foi completamente reestruturado para uma arquitetura baseada em serviços Python.

Durante a refatoração foram eliminadas todas as dependências de scraping e automação de interface, tornando a solução mais estável, rastreável e adequada para execuções em larga escala.

---

# Autor

Leonardo Matsubara

Analista de Tecnologia Educacional Sênior