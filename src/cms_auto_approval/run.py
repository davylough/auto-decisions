from flytekit import task
from pathlib import Path
import pandas as pd
from src.cms_auto_approval.pipelines.data_engineering_mumford_data.nodes import preprocess_mumford_data
from src.cms_auto_approval.pipelines.data_science_mumford_data.nodes import train_model

@task
def run_package():
    df = pd.read_csv('auto-decisions/src/data/01_raw/small.csv')
    pre_pro_df = preprocess_mumford_data(df)
    model = train_model(pre_pro_df)
    return modelx


if __name__ == "__main__":
    run_package()
