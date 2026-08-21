"""
Serviços de migração seletiva do Canvas.
"""

import difflib

from config import (
    PAGE_KEYWORDS,
    CRITICAL_TERMS,
    GREEN,
    RED,
    YELLOW,
    RESET
)


# ==========================================================
# NORMALIZAÇÃO DOS BANCOS
# ==========================================================

def get_target_name(original_name):
    """
    Identifica bancos de questões válidos.
    """

    name_clean = str(original_name).strip()
    name_norm = name_clean.lower()

    # Dissertativa

    if "dissert" in name_norm:
        return "Atv. Dissertativa"

    # Objetivas

    if "obj" in name_norm:

        if "2" in name_norm:
            return "Atv. Objetiva 2"

        if "3" in name_norm:
            return "Atv. Objetiva 3"

        if "4" in name_norm:
            return "Atv. Objetiva 4"

        return "Atv. Objetiva"

    # Provas

    if "prova" in name_norm:

        if "ao2" in name_norm:
            return "Prova AO2"

        if "subst" in name_norm:
            return "Prova Substitutiva"

    # Similaridade

    closest = difflib.get_close_matches(
        name_clean,
        CRITICAL_TERMS,
        n=1,
        cutoff=0.5
    )

    if closest:
        return closest[0]

    return None


# ==========================================================
# PAYLOAD AUXILIAR
# ==========================================================

def add_to_nested_payload(payload, item):

    item_type = item.get("type")
    migration_id = item.get("migration_id")

    if not item_type or not migration_id:
        return

    if item_type not in payload["copy"]:
        payload["copy"][item_type] = {}

    payload["copy"][item_type][
        f"id_{migration_id}"
    ] = "1"


def get_keys_recursive(items, payload, log_list):

    for item in items:

        if not isinstance(item, dict):
            continue

        add_to_nested_payload(payload, item)

        if item.get("type") == "attachments":
            log_list.append(
                item.get("title", "Sem título")
            )

        sub_items = item.get("sub_items")

        if sub_items:
            get_keys_recursive(
                sub_items,
                payload,
                log_list
            )


# ==========================================================
# FILTRO DE ITENS
# ==========================================================

def filter_selective_data(
    client,
    migration_url,
    types_to_include
):
    """
    Filtra o conteúdo que será migrado.
    """

    selection_payload = {
        "copy": {}
    }

    stats = {
        "wiki_pages": [],
        "attachments": [],
        "assessment_question_banks": []
    }

    for data_type in types_to_include:

        print(f"   -> Mapeando {data_type}...")

        next_url = (
            f"{migration_url}/selective_data"
        )

        params = {
            "type": data_type,
            "per_page": 100
        }

        full_data = []

        while next_url:

            response = client.get(
                next_url,
                params=params
            )

            if response.status_code != 200:

                print(
                    f"{RED}[ERRO] Falha ao carregar "
                    f"{data_type}{RESET}"
                )

                break

            full_data.extend(
                response.json()
            )

            if "next" in response.links:

                next_url = (
                    response.links["next"]["url"]
                )

                params = {}

            else:
                next_url = None

        # ATTACHMENTS

        if data_type == "attachments":

            get_keys_recursive(
                full_data,
                selection_payload,
                stats["attachments"]
            )

            print(
                f"      [+] "
                f"{len(stats['attachments'])} arquivos"
            )

            continue

        # PAGES E BANKS

        for item in full_data:

            if not isinstance(item, dict):
                continue

            title = str(
                item.get("title", "")
            )

            selected = False

            if data_type == "wiki_pages":

                selected = any(
                    keyword.lower()
                    in title.lower()
                    for keyword in PAGE_KEYWORDS
                )

            elif data_type == "assessment_question_banks":

                selected = (
                    get_target_name(title)
                    is not None
                )

            if selected:

                add_to_nested_payload(
                    selection_payload,
                    item
                )

                stats[data_type].append(
                    title
                )

                tipo = (
                    "BANCO"
                    if data_type == "assessment_question_banks"
                    else "PÁGINA"
                )

                print(
                    f"      [+] {tipo}: {title}"
                )

    return selection_payload, stats


# ==========================================================
# CONTENT MIGRATION
# ==========================================================

def execute_selective_migration(
    client,
    target_course_id,
    source_course_id,
    types_to_import
):
    """
    Executa uma migração seletiva.
    """

    payload = {
        "migration_type": "course_copy_importer",
        "settings": {
            "source_course_id": source_course_id
        },
        "selective_import": True
    }

    response = client.post(
        f"/courses/{target_course_id}/content_migrations",
        json=payload
    )

    if response.status_code not in [200, 201]:

        print(
            f"{RED}Erro ao iniciar migração:{RESET}"
        )
        print(response.text)

        return None

    migration_id = response.json()["id"]

    migration_url = (
        f"{client.base_url}/courses/"
        f"{target_course_id}/content_migrations/"
        f"{migration_id}"
    )

    if not client.wait_for_migration_state(
        migration_url,
        "waiting_for_select"
    ):
        return None

    print("   -> Filtrando conteúdo...")

    selection_payload, stats = (
        filter_selective_data(
            client,
            migration_url,
            types_to_import
        )
    )

    total_items = sum(
        len(v)
        for v in selection_payload["copy"].values()
    )

    if total_items == 0:

        print(
            f"{YELLOW}Nenhum item encontrado.{RESET}"
        )

        return None

    print(
        f"{GREEN}Total selecionado: "
        f"{total_items}{RESET}"
    )

    finish = client.put(
        migration_url,
        json=selection_payload
    )

    if finish.status_code != 200:

        print(
            f"{RED}Erro ao enviar seleção."
            f"{RESET}"
        )

        return None

    print(
        f"{GREEN}Migração enviada com sucesso."
        f"{RESET}"
    )

    return stats