"""
Configurações globais do Canvas Migrator
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================================
# CANVAS
# ==========================================================

CANVAS_API_URL = "https://famonline.instructure.com/api/v1"

# Recomendo usar variável de ambiente
TOKEN = os.getenv("CANVAS_TOKEN")

VERIFY_SSL = False
ACCOUNT_ID = 1

# ==========================================================
# ARQUIVOS
# ==========================================================

MIGRATION_LIST = "inputs/oferta_disciplinas_manual.xlsx"

SHEET_NAME = "Geral"

SKIP_ROWS = 0
LIMIT = 0

# ==========================================================
# LOGS
# ==========================================================

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
ORANGE = "\033[94m"
GRAY = "\033[90m"
RESET = "\033[0m"

# ==========================================================
# FILTROS DE PÁGINAS
# ==========================================================

PAGE_KEYWORDS = [
    "e-book",
    "material adicional",
    "tópico",
    "podcast",
    "vídeo |",
    "material adicional | tópico",
    "aulas gravadas",
    "vídeos e-book"
]

# ==========================================================
# TERMOS CRÍTICOS (BDQ)
# ==========================================================

CRITICAL_TERMS = [
    "Atv. Dissertativa",
    "Atv. Objetiva",
    "Atv. Objetiva 2",
    "Atv. Objetiva 3",
    "Atv. Objetiva 4",
    "Prova AO2",
    "Prova Substitutiva"
]

# ==========================================================
# ORGANIZAÇÃO DE MÓDULOS
# ==========================================================

TOPICS_ORDER = {
    r"^topico\s+\d+\s*-\s*podcast": 93,
    r"^t[oó]pico\s+\d+\s*-\s*podcast": 93,
    r"^t[óo]pico(\s+de\s+estudo)?\s+\d+": 90,

    r"^ebook\s*\|\s*t[óo]pico": 91,
    r"^e-book\s*\|\s*t[óo]pico": 91,

    r"^material\s+adicional\s*\|\s*t[óo]pico": 92,

    r"^podcast\s*\|\s*t[óo]pico": 93,

    r"^v[íi]deo\s*\|\s*t[óo]pico": 94,

    r"^v[íi]deos?\s+e-?book": 95,

    r"^atividade\b": 999
}

# ==========================================================
# STATUS SEM MOVIMENTAÇÃO
# ==========================================================

PUBLISH_ONLY_PATTERNS = [
    r"^ao2\b",
    r"^ao2\s+substitutiva\b",
    r"^revisão\s+de\s+notas\s*\|\s*ao"
]

# ==========================================================
# RATE LIMIT PARA PROTEÇÃO
# ==========================================================
REQUEST_DELAY = 0.25
RATE_LIMIT_RETRY_SECONDS = 30
MAX_RATE_LIMIT_RETRIES = 10
