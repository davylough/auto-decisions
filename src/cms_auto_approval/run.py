from flytekit import task
import boto3
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import pandas as pd
from src.cms_auto_approval.pipelines.data_engineering_mumford_data.nodes import preprocess_mumford_data
from src.cms_auto_approval.pipelines.data_science_mumford_data.nodes import train_model

@task
def run_package():

    # read training dataset from S3
    s3_client = boto3.client("s3")
    obj = s3_client.get_object(Bucket= "bv-ml-ops", Key= "pipelines/auto-decisions/200000.csv") 
    df = pd.read_csv(obj['Body'])

    # pre-process data and train model
    pre_pro_df = preprocess_mumford_data(df)
    model = train_model(pre_pro_df)

    # save model to S3
    s3_resource = boto3.resource("s3")
    initial_type = [('float_input', FloatTensorType((1, 14)))]
    onnx_model = convert_sklearn(model, initial_types=initial_type)
    onnx_model_ser = onx.SerializeToString()
    s3_resource.Object("bv-ml-ops","pipelines/auto-decisions/model.onnx").put(Body=onnx_model_ser)

    return model


if __name__ == "__main__":
    run_package()
