from flytekit import task
import boto3
from pathlib import Path
import pandas as pd
from src.cms_auto_approval.pipelines.data_engineering_mumford_data.nodes import preprocess_mumford_data
from src.cms_auto_approval.pipelines.data_science_mumford_data.nodes import train_model

@task
def run_package():
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket= "bv-ml-ops/pipelines/auto-decisions", Key= "200000.csv") 
    df = pd.read_csv(obj['Body'])
    print(df.head())

    #df = pd.read_csv('auto-decisions/src/data/01_raw/200000.csv')
    pre_pro_df = preprocess_mumford_data(df)
    model = train_model(pre_pro_df)
    return model


if __name__ == "__main__":
    run_package()
