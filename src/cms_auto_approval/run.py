from flytekit import task

"""Application entry point."""
from pathlib import Path
import pandas as pd

@task
def run_package():
    print("yeet1")
    df = pd.read_csv('~/auto-decisions/data/01_raw/small.csv')
    
    return df.head()


if __name__ == "__main__":
    run_package()
