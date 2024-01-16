from flytekit import task
import flytekit

"""Application entry point."""
from pathlib import Path
import pandas as pd
import os

@task
def run_package():
    print("yeet1")
    print(os.listdir())
    print(os.listdir('auto-decisions'))
    
    #df = pd.read_csv(csv_path)
    #print(df.head)
    #return df.head()


if __name__ == "__main__":
    run_package()
