from flytekit import task
import flytekit

"""Application entry point."""
from pathlib import Path
import pandas as pd
import os

@task
def run_package():
    print("yeet1")
    print(flytekit.current_context().working_directory)
    csv_path = os.path.join(
        flytekit.current_context().working_directory,
        f"normalized-{os.path.basename(csv_url.path).rsplit('.')[0]}.csv",
    )
    df = pd.read_csv(csv_path)
    print(df.head())
    return df.head()


if __name__ == "__main__":
    run_package()
