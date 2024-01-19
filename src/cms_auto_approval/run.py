from flytekit import task
import boto3
from pathlib import Path
import pandas as pd
from skl2onnx import convert_sklearn
from src.cms_auto_approval.pipelines.data_engineering_mumford_data.nodes import preprocess_mumford_data
from src.cms_auto_approval.pipelines.data_science_mumford_data.nodes import train_model

@task
def run_package():
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket= "bv-ml-ops", Key= "pipelines/auto-decisions/200000.csv") 
    df = pd.read_csv(obj['Body'])

    pre_pro_df = preprocess_mumford_data(df)
    model = train_model(pre_pro_df)
    onnx_model = convert_sklearn(model)

    s3.put_object(Body= onnx_model, Bucket= "bv-ml-ops", Key= "pipelines/auto-decisions/model.onnx")
    return model


if __name__ == "__main__":
    run_package()
