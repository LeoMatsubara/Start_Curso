import os
from datetime import datetime


def generate_timestamp():
    return datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

def save_reports(
    processed_df,
    failed_df,
    missing_bdq_df,
    output_folder="outputs"
):
    os.makedirs(
        output_folder,
        exist_ok=True
    )

    timestamp = generate_timestamp()

    processed_df.to_excel(
        f"{output_folder}/{timestamp}_migration_processed.xlsx",
        index=False
    )

    failed_df.to_excel(
        f"{output_folder}/{timestamp}_migration_failed.xlsx",
        index=False
    )

    missing_bdq_df.to_excel(
        f"{output_folder}/{timestamp}_migration_missing_bdq.xlsx",
        index=False
    )

    print(
        "\nRelatórios gerados com sucesso."
    )