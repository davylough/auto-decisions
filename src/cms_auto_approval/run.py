from flytekit import task

"""Application entry point."""
from pathlib import Path
import pandas as pd
import os

@task
def run_package():
    print("yeet1")
    #df = pd.read_csv('~/data/01_raw/small.csv')
    cwd = os.getcwd()
    #return df.head()
    return cwd


if __name__ == "__main__":
    run_package()
