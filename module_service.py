"""
Serviços de organização dos módulos.
"""

import time
import re
from turtle import title

from config import (
    TOPICS_ORDER,
    PUBLISH_ONLY_PATTERNS,
    GREEN,
    RED,
    GRAY,
    RESET
)

import unicodedata

def normalize_text(text):
    return "".join(
        c
        for c in unicodedata.normalize(
            "NFD",
            str(text)
        )
        if unicodedata.category(c) != "Mn"
    ).lower()


def get_absolute_position(title, order_map=TOPICS_ORDER):
    """
    Retorna a posição alvo do item.
    """

    title_clean = title.lower().strip()

    for pattern, position in order_map.items():

        if re.match(pattern, title_clean):
            return position

    return None

def is_publish_only(title):
    """
    Define itens que apenas alteram status.
    """

    title_clean = title.lower().strip()

    return any(
        re.match(pattern, title_clean)
        for pattern in PUBLISH_ONLY_PATTERNS
    )

def get_item_status(title):
    """
    Define se o item deve ficar publicado.
    """

    title_clean = title.lower().strip()

    if re.match(r"^atividade\b", title_clean):
        return False

    if re.match(r"^ao2\b", title_clean):
        return False

    return True

def ensure_topic_pages_presence(
    client,
    course_id,
    modules,
    order_map
):
    """
    Garante que páginas de Tópico ou Tópico de Estudo
    sejam inseridas nos módulos correspondentes.
    """

    print("   -> Verificando páginas de tópicos...")

    pages = []
    next_url = f"/courses/{course_id}/pages"

    try:

        while next_url:

            response = client.get(
                next_url,
                params={"per_page": 100}
            )

            if response.status_code != 200:
                break

            pages.extend(response.json())

            if "next" in response.links:
                next_url = response.links["next"]["url"]
            else:
                next_url = None

        for page in pages:

            title = page.get("title", "")

            if "topico" not in normalize_text(title):
                continue

            match_num = re.search(r"(\d+)", title)

            if not match_num:
                continue

            topic_number = match_num.group(1)

            pattern_module = rf"topico\s*0?{topic_number}\b"

            target_module = next(
                (
                    module
                    for module in modules
                    if re.search(
                        pattern_module,
                        normalize_text(module["name"])
                    )
                ),
                None
            )

            if not target_module:
                continue

            final_position = (
                get_absolute_position(
                    title,
                    order_map
                )
                or 90
            )

            endpoint = (
                f"/courses/{course_id}/modules/"
                f"{target_module['id']}/items"
            )

            existing_response = client.get(endpoint)

            if existing_response.status_code != 200:
                continue

            current_items = existing_response.json()

            already_exists = any(
                item.get("page_url") == page["url"]
                for item in current_items
            )

            if already_exists:
                continue

            payload = {
                "module_item": {
                    "title": title,
                    "type": "Page",
                    "page_url": page["url"],
                    "position": final_position,
                    "indent": 1,
                    "published": True
                }
            }

            client.post(
                endpoint,
                json=payload
            )

            print(
                f"[+] {title} inserido em "
                f"{target_module['name']}"
            )

    except Exception as exc:

        print(
            f"[ERRO AO INSERIR TÓPICOS] {exc}"
        )

def ensure_aulas_gravadas_in_aulas_module(
    client,
    course_id,
    modules
):
    """
    Garante que TODAS as páginas chamadas
    'Aulas Gravadas' estejam inseridas
    no módulo 'Aulas'.
    """

    print("   -> Verificando páginas Aulas Gravadas...")

    response = client.get(
        f"/courses/{course_id}/pages",
        params={
            "search_term": "Aulas Gravadas",
            "per_page": 100
        }
    )

    if response.status_code != 200:
        return

    pages = [
        page
        for page in response.json()
        if page.get("title", "").strip().lower()
        == "aulas gravadas"
    ]

    print(
        f"      Encontradas {len(pages)} páginas "
        f"'Aulas Gravadas'"
    )

    if not pages:
        return

    aulas_module = next(
        (
            module
            for module in modules
            if module["name"].strip().lower()
            == "aulas"
        ),
        None
    )

    if not aulas_module:

        print(
            "[AVISO] Módulo 'Aulas' não encontrado."
        )

        return

    endpoint = (
        f"/courses/{course_id}/modules/"
        f"{aulas_module['id']}/items"
    )

    response = client.get(endpoint)

    if response.status_code != 200:
        return

    current_items = response.json()

    for page in pages:

        page_url = page["url"]

        already_linked = any(
            item.get("page_url") == page_url
            for item in current_items
        )

        if already_linked:
            continue

        payload = {
            "module_item": {
                "title": page["title"],
                "type": "Page",
                "page_url": page_url,
                "published": True
            }
        }

        result = client.post(
            endpoint,
            json=payload
        )

        if result.status_code in [200, 201]:

            print(
                f"[+] Página adicionada ao módulo "
                f"Aulas ({page_url})"
            )

        else:

            print(
                f"[ERRO] Falha ao inserir "
                f"{page_url}"
            )
            
def organize_course_modules(client, course_id, order_map=None):
    """
    Organiza posições e status de publicação dos itens dos módulos.
    """

    if order_map is None:
        order_map = TOPICS_ORDER

    print(
        f"\n-> Organizando módulos do curso {course_id}"
    )

    try:

        response = client.get(
            f"/courses/{course_id}/modules",
            params={"per_page": 100}
        )

        if response.status_code != 200:

            print(
                f"{RED}[ERRO] Não foi possível "
                f"obter módulos.{RESET}"
            )

            return

        modules = response.json()

        for module in modules:

            module_id = module["id"]

            endpoint = (
                f"/courses/{course_id}/modules/"
                f"{module_id}/items"
            )

            response = client.get(
                endpoint,
                params={"per_page": 100}
            )

            if response.status_code != 200:
                continue

            items = response.json()

            for item in items:

                title = item.get("title", "")
                item_id = item.get("id")

                new_position = get_absolute_position(
                    title,
                    order_map
                )

                published = get_item_status(
                    title
                )

                status_label = (
                    "Publicado"
                    if published
                    else "Despublicado"
                )

                # -------------------------------------------------
                # ITENS QUE DEVEM SER REPOSICIONADOS
                # -------------------------------------------------

                if new_position is not None:

                    payload = {
                        "module_item": {
                            "position": new_position,
                            "indent": (
                                1
                                if "Tópico" in title
                                else 0
                            ),
                            "published": published
                        }
                    }

                    client.put(
                        f"{endpoint}/{item_id}",
                        json=payload
                    )

                    print(
                        f"{GREEN}[M] "
                        f"{title} -> "
                        f"Pos {new_position} "
                        f"({status_label})"
                        f"{RESET}"
                    )

                # -------------------------------------------------
                # SOMENTE PUBLICAÇÃO
                # -------------------------------------------------

                elif is_publish_only(title):

                    payload = {
                        "module_item": {
                            "published": published
                        }
                    }

                    client.put(
                        f"{endpoint}/{item_id}",
                        json=payload
                    )

                    print(
                        f"{GREEN}[M] "
                        f"{title} -> "
                        f"{status_label}"
                        f"{RESET}"
                    )

                # -------------------------------------------------
                # IGNORADOS
                # -------------------------------------------------

                else:

                    print(
                        f"{GRAY}[IGNORADO] "
                        f"{title}"
                        f"{RESET}"
                    )

        # ---------------------------------------------
        # Pós-processamento
        # ---------------------------------------------

        ensure_aulas_gravadas_in_aulas_module(
            client,
            course_id,
            modules
        )

        ensure_topic_pages_presence(
            client,
            course_id,
            modules,
            order_map
        )

    except Exception as exc:

        print(
            f"{RED}[ERRO CRÍTICO] "
            f"{exc}"
            f"{RESET}"
        )

def run_module_organization(
    client,
    dataframe,
    order_map=None
):
    """
    Organiza os módulos dos cursos processados.
    """

    if order_map is None:
        order_map = TOPICS_ORDER

    dataframe = dataframe.drop_duplicates(
        subset=["course_id"],
        keep="first"
    )

    for row in dataframe.itertuples():

        print(
            f"\nDisciplina: "
            f"{row.course} "
            f"({row.identifier})"
        )

        try:

            while client.has_running_migrations(
                row.course_id
            ):

                print(
                    "[AGUARDANDO] Migração em execução...",
                    end="\r"
                )

                time.sleep(10)

            print(
                "\nMigração concluída. "
                "Iniciando organização."
            )

            organize_course_modules(
                client=client,
                course_id=row.course_id,
                order_map=order_map
            )

        except Exception as exc:

            print(
                f"[ERRO] {exc}"
            )