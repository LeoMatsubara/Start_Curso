import pandas as pd
import time

from config import (
    MIGRATION_LIST,
    SHEET_NAME,
    SKIP_ROWS,
    LIMIT,
    TOPICS_ORDER,
    ORANGE,
    GREEN,
    YELLOW,
    RED,
    GRAY,
    RESET
)

from canvas_client import CanvasClient

from migration_service import (
    execute_selective_migration
)

from module_service import (
    organize_course_modules
)

from report_service import (
    save_reports
)

from checkpoint_service import (
    load_checkpoint,
    save_checkpoint
)

from logger import (
    configure_logger
)

# ==========================================================
# LOAD DATA
# ==========================================================

def load_migrations():

    df = pd.read_excel(
        MIGRATION_LIST,
        sheet_name=SHEET_NAME
    )

    df = df.dropna(subset=["LINK"])
    df = df.fillna("")

    if SKIP_ROWS:
        df = df.iloc[SKIP_ROWS:]

    if LIMIT:
        df = df.iloc[:LIMIT]

    return df

# ==========================================================
# FORMATAÇÂO DE TEMPO
# ==========================================================

def format_duration(seconds):

    hours = int(seconds // 3600)

    minutes = int(
        (seconds % 3600) // 60
    )

    return (
        f"{hours:02d}h "
        f"{minutes:02d}m"
    )

# ==========================================================
# MAIN
# ==========================================================

def main():

    logger = configure_logger()

    start_global = time.time()
    processed_count = 0

    client = CanvasClient()

    migrations = load_migrations()

    processed = []
    failed = []
    missing_bdq = []

    total = len(migrations)

    processed_courses = load_checkpoint()

    for index, row in enumerate(
        migrations.itertuples(index=False),
        start=1
    ):
        course_start_time = time.time()
        identifier = str(row.IDENTIFICADOR)

        if identifier in processed_courses:
            print(
                f"[SKIP] {identifier} "
                f"já processado anteriormente."
            )
            continue

        print(
            f"\n{ORANGE}"
            f"{index}/{total}"
            f" | "
            f"{row.DISCIPLINA}"
            f" - "
            f"{row.IDENTIFICADOR}"
            f"{RESET}"
        )

        logger.info(
            f"Iniciando disciplina "
            f"{row.IDENTIFICADOR}"
        )

        try:

            target_course_id = (
                client.get_course_id(
                    row.IDENTIFICADOR
                )
            )

            if not target_course_id:

                print(
                    f"{YELLOW}"
                    f"Destino não encontrado."
                    f"{RESET}"
                )

                continue

            link_ref = str(row.LINK).strip()
            bdq_ref = str(row.BDQ).strip()

            link_source = (
                f"sis_course_id:{link_ref}"
                if not link_ref.isdigit()
                else link_ref
            )

            bdq_source = (
                f"sis_course_id:{bdq_ref}"
                if not bdq_ref.isdigit()
                else bdq_ref
            )

            tasks = []

            if link_ref == bdq_ref:

                tasks.append(
                    {
                        "source": link_source,
                        "label": "GERAL",
                        "types": [
                            "wiki_pages",
                            "attachments",
                            "assessment_question_banks"
                        ]
                    }
                )

            else:

                tasks.extend(
                    [
                        {
                            "source": link_source,
                            "label": "CONTEÚDO",
                            "types": [
                                "wiki_pages",
                                "attachments"
                            ]
                        },
                        {
                            "source": bdq_source,
                            "label": "BDQ",
                            "types": [
                                "assessment_question_banks"
                            ]
                        }
                    ]
                )

            total_pages = 0
            total_files = 0
            total_bdq = 0

            for task in tasks:

                print(
                    f"\n-> {task['label']}"
                )

                stats = execute_selective_migration(
                    client=client,
                    target_course_id=target_course_id,
                    source_course_id=task["source"],
                    types_to_import=task["types"]
                )

                if not stats:
                    continue

                total_pages += len(
                    stats["wiki_pages"]
                )

                total_files += len(
                    stats["attachments"]
                )

                total_bdq += len(
                    stats["assessment_question_banks"]
                )

            metadata = {
                "course_id": target_course_id,
                "identifier": row.IDENTIFICADOR,
                "course": row.DISCIPLINA,
                "page_count": total_pages,
                "bdq_count": total_bdq,
                "file_count": total_files,
                "link": row.LINK,
                "bdq": row.BDQ
            }

            processed.append(metadata)

            print(
                "\nAguardando conclusão da migração..."
            )

            while client.has_running_migrations(
                target_course_id
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
                course_id=target_course_id,
                order_map=TOPICS_ORDER
            )

            course_seconds = (
                time.time() - course_start_time
            )
            processed_count += 1

            elapsed_global = (
                time.time() - start_global
            )

            avg_seconds = (
                elapsed_global /
                processed_count
            )

            remaining_courses = (
                total - processed_count
            )

            eta_seconds = (
                avg_seconds *
                remaining_courses
            )

            print(
                f"\n[PROGRESSO] "
                f"{processed_count}/{total} | "
                f"Curso: {course_seconds:.1f}s | "
                f"Média: {avg_seconds:.1f}s | "
                f"ETA: {format_duration(eta_seconds)}"
            )

            logger.info(
                f"Progresso "
                f"{processed_count}/{total} | "
                f"Curso {course_seconds:.1f}s | "
                f"Média {avg_seconds:.1f}s | "
                f"ETA {format_duration(eta_seconds)}"
            )

            save_checkpoint(
                identifier=row.IDENTIFICADOR,
                status="SUCCESS"
            )

            logger.info(
                f"{row.IDENTIFICADOR} "
                f"processada com sucesso"
            )

            if total_bdq <= 0:
                missing_bdq.append(metadata)

            print(
                f"{GREEN}"
                f"Curso processado."
                f"{RESET}"
            )

        except Exception as exc:

            print(
                f"{RED}"
                f"Erro crítico: {exc}"
                f"{RESET}"
            )

            failed.append(
                row._asdict()
            )

            save_checkpoint(
                identifier=row.IDENTIFICADOR,
                status="FAILED"
            )

            logger.exception(
                f"Erro na disciplina "
                f"{row.IDENTIICADOR}"
            )

    # ======================================================
    # DATAFRAMES
    # ======================================================

    processed_df = pd.DataFrame(processed)

    failed_df = pd.DataFrame(failed)

    missing_bdq_df = pd.DataFrame(
        missing_bdq
    )

    # ======================================================
    # REPORTS
    # ======================================================

    save_reports(
        processed_df=processed_df,
        failed_df=failed_df,
        missing_bdq_df=missing_bdq_df
    )

    # ======================================================
    # MODULES
    # ======================================================

    logger.info(
    "Processo finalizado."
    )

    print(
        f"\n{GRAY}"
        f"Processo finalizado."
        f"{RESET}"
    )

    total_time = time.time() - start_global

    print("\n===== RESUMO =====")

    print(
        f"Disciplinas processadas: "
        f"{processed_count}"
    )

    print(
        f"Falhas: "
        f"{len(failed_df)}"
    )

    print(
        f"Sem BDQ: "
        f"{len(missing_bdq_df)}"
    )

    print(
        f"Tempo total: "
        f"{format_duration(total_time)}"
    )


if __name__ == "__main__":
    main()