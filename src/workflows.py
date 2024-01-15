from typing import Tuple
from unittest import result

import pandas as pd
from flytekit import workflow

from src.cms_auto_approval.run import run_package
from src.tasks.reporting import experiment_tracker_file, track_experiment_results
from src.types import CachedDataFrame

#
# Your workflows should follow the structure of "Kedro's data engineering convention" as discussed
# here: https://bazaarvoice.atlassian.net/wiki/spaces/DEV/pages/78087192634/MLOps+Step+2+Data+Preparation#Data-Engineering-for-Machine-Learning
# Below some example workflows are defined.


@workflow
def process_raw_data() -> CachedDataFrame:
    """
    Processes raw data from facts storage for the auto-decisions project.

    Raw data may be stored on s3, require a joule or athena job to run, or be gathered from some other immutable, reproducible store.

    Which data produced by this workflow depends on your project (see the "data engineering convention" above), but should be either:
        - intermediate: Typed representation of the raw layer e.g. converting string based values into their current typed representation
                        as numbers, dates etc.
        - primary: Domain specific data model(s) containing cleansed, transformed and wrangled data from either raw or intermediate,
                   which forms your layer that can be treated as the workspace for any feature engineering down the line.
        - feature: Analytics specific data model(s) containing a set of features defined against the primary data, which are grouped by
                   feature area of analysis. In practice this covers the independent variables and target variable which will form the basis
                   for ML exploration and application.

    If this pipeline is not returning "feature" data, you should add new pipelines below.
    """
    ...


@workflow
def generate_model_input(
    features: CachedDataFrame,
) -> Tuple[CachedDataFrame, CachedDataFrame, CachedDataFrame]:
    """
    Creates inputs for training models in the auto-decisions project.

    This workflow will take your features and create inputs to your model training proceedure. This may be as complicated as packing images or text into
    formats to make training more efficient (like recordio), or as basic as simply peforming a train/test/validation split.
    (see https://bazaarvoice.atlassian.net/wiki/spaces/DEV/pages/78087192634/MLOps+Step+2+Data+Preparation#Train,-Validation,-And-Test-Data).
    The workflow should return 3 datasets: train, test, and validation, respectively.

    Adjust the return type to your needs here -- you may need to return FlyteFile if you plan on using sagemaker training code.

    Args:
        features(CachedDataFrame):  Analytics specific data model(s) containing a set of features defined against the primary data.
    Returns:
        A 3 tuple containing training, test, and validation data sets (respectively).
    """
    ...


@workflow
def train_model(
    training_data: CachedDataFrame, validation_data: CachedDataFrame
) -> str:
    """
    Trains the model for auto-decisions.

    This function should return stored, serialized pre-trained machine learning models. In the simplest case, these are stored as something like a
    pickle file (and thus this function should return FlyteFile). If you plan on using the model deployment service, this function should return the
    model version identifier.

    Args:
        training_data(CachedDataFrame): The sample of data used to fit the model.
        validation_data(CachedDataFrame): The sample of data used to provide an unbiased evaluation of a model fit on the training dataset while
                                          tuning model hyperparameters, performing early stopping, etc. The evaluation becomes more biased as skill
                                          on the validation dataset is incorporated into the model configuration.
    Returns:
        str: A serialized, trained machine learning model in the form of a model version identifier from the model deployment service.
    """
    ...


@workflow
def generate_model_output(model: str, test_data: CachedDataFrame) -> CachedDataFrame:
    """
    Performs inference on the provided data given a specific model artfact for auto-decisions.

    This workflow generates model outputs of the provided data for analysis. This can often take many hours depending on the
    size of the data and the complexity of the trained model.

    Args:
        model(str): The identifier to the model to use for inference.
        test_data(CachedDataFrame): The data to perform inference on.
    Returns:
        CachedDataFrame: A dataset containing the input data along with model outputs.
    """
    ...


@workflow
def reporting(model: str, model_output: CachedDataFrame) -> pd.DataFrame:
    """
    Generates a performance and accuracy report for the provided model output of auto-decisions.

    This workflow should be used for outputting analyses or modeling results that are often Ad Hoc or simply descriptive reports.
    At the most basic level, this workflow should produce the KPI or model accuracy measure that you're using to measure "goodness".
    It's often more valuable to get more complex here -- including returning multiple metrics (like accuracy, tpr, fpr, etc for classifiers),
    generating graphs or charts (like precision-recall curves, ROCs, etc), or even tracking experiments across models by storing a dataframe
    in a fixed location and augmenting it each run.

    Args:
        model(str): The model that was evaluated.
        model_output(CachedDataFrame): The outputs generated by the model on the test data.
    Returns:
        pd.DataFrame: A table of relevant statistics for this model (and previous ones)
    """

    # Commmon things you may want to do is compute the accuracy and use the experiment tracker
    accuracy = ...
    
    _, experiment_result_df = track_experiment_results(
        result_file=experiment_tracker_file(),
        model=model,
        accuracy=accuracy
    )
    return experiment_result_df


@workflow
def evaluate(model: str, test_data: CachedDataFrame) -> pd.DataFrame:
    """
    A convenience pipeline for evaluating models in auto-decisions.

    This workflow evaluates a model and reports on it's accuracy. It is convenient to provide this interface for evaluating
    existing models or previous models against new test data.

    Args:
        model(str): The model to evaluate
        test_data(CachedDataFrame): The test data to evaluate the model on
    Returns:
        The result of the reporting pipeline
    """
    model_outputs = generate_model_output(model=model, test_data=test_data)
    return reporting(model=model, model_output=model_outputs)


@workflow
def full() -> pd.DataFrame:
    """
    A complete flyte pipeline for training models for auto-decisions.

    This workflow should compose all of the above workflows into a final pipeline that trains a new model and reports on it's accuracy.
    If your raw data requires arguments, you this workflow should too.
    """
    feature_data = process_raw_data()
    training_data, validation_data, test_data = generate_model_input(
        features=feature_data
    )
    model_artifact = train_model(
        training_data=training_data, validation_data=validation_data
    )
    return evaluate(model=model_artifact, test_data=test_data)


@workflow
def my_wf():
    """
    This is simply an example workflow to get you started with flyte...
    You can erase this if you don't need it.
    """
    res = run_package()
    print("yeet2")
    return res


if __name__ == "__main__":
    print(f"Running my_wf() {my_wf()}")
