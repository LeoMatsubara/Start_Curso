import os
import pandas as pd


CHECKPOINT_FILE = "outputs/checkpoint.csv"

def save_checkpoint(identifier, status):
    """
    Salva disciplinas processadas.
    """
    os.makedirs("outputs", exist_ok=True)
    row = pd.DataFrame([
        {
            "identifier": identifier,
            "status": status
        }
    ])

    if os.path.exists(CHECKPOINT_FILE):
        row.to_csv(
            CHECKPOINT_FILE,
            mode="a",
            header=False,
            index=False
        )
    else:
        row.to_csv(CHECKPOINT_FILE, index=False)

def load_checkpoint():

    if not os.path.exists(CHECKPOINT_FILE):
        return set()

    df = pd.read_csv(CHECKPOINT_FILE)

    return set(df["identifier"].astype(str).tolist())