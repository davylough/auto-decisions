from flytekit import task
import boto3
import io
from pathlib import Path
import pandas as pd
import pickle
from src.cms_auto_approval.pipelines.data_engineering_mumford_data.nodes import preprocess_mumford_data
from src.cms_auto_approval.pipelines.data_science_mumford_data.nodes import train_model

@task
def run_package():
    s3_client = boto3.client("s3")
    obj = s3_client.get_object(Bucket= "bv-ml-ops", Key= "pipelines/auto-decisions/200000.csv") 
    df = pd.read_csv(obj['Body'])
    pre_pro_df = preprocess_mumford_data(df)
    model = train_model(pre_pro_df)

    #pickle_buffer = io.BytesIO()
    s3_resource = boto3.resource("s3")
    #new_df.to_pickle(pickle_buffer)
    
    pickle_obj = pickle.dump(model, open("auto_decisions_model.pickle", "wb"))
    s3_resource.Object("bv-ml-ops","pipelines/auto-decisions/model.onnx").put(Body=pickle_obj)
    #s3.put_object(Body= loaded_model, Bucket= "bv-ml-ops", Key= "pipelines/auto-decisions/model.onnx")
    return model


if __name__ == "__main__":
    run_package()
