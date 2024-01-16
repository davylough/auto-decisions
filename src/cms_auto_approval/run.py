from flytekit import task

"""Application entry point."""
from pathlib import Path
import pandas as pd
import os

@task
def run_package():
    print("yeet1")
    print(os.listdir('/auto-decisions'))
    #df = pd.read_csv('~/auto-decisions/data/01_raw/small.csv')
    
    #return df.head()


if __name__ == "__main__":
    run_package()
