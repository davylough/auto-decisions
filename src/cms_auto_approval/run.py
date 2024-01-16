from flytekit import task
import flytekit

"""Application entry point."""
from pathlib import Path
import pandas as pd
import os

@task
def run_package():
    print("yeet1")
    
    df = pd.read_csv('auto-decisions/src/data/01_raw/small.csv')
    print(df.head)
    return df.head()


if __name__ == "__main__":
    run_package()
