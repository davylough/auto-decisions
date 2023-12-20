import logging
from typing import Optional, Tuple

import flytekit
import pandas as pd
from flytekit import task
from flytekit.deck.renderer import TopFrameRenderer
from flytekit.types.file import FlyteFile
from src.config import constants
from typing_extensions import Annotated

logging.basicConfig(level=logging.INFO)

def experiment_tracker_file() -> FlyteFile:
    return FlyteFile(constants.reporting.experiment_tracker)


def _track_experiment_results(
    result_file: FlyteFile, model: str, **kwargs
) -> Tuple[FlyteFile, Annotated[pd.DataFrame, TopFrameRenderer(10)]]:
    """
    This function tracks results for the auto-decisions project. It records all results in a dataframe that is persisted on s3.
    Each time this function is called, the results are appended to the existing dataframe.

    To use it, simply pass in your relevant statistics into the arguments:

    _track_experiment_results(
        result_file = experiment_tracker_file(),
        model = model_artifact,
        accuracy = computed_accuracy,
        true_positive_rate = computed_tpr,
        ....
    )
    """

    # Try to load the existing file
    try:
        df = pd.read_csv(result_file.download())
    except Exception as e:
        logging.warning(
            f"Could not load results file {result_file.path} : {result_file.remote_source}"
        )
        df = None

    # generate a new dataframe
    execution_id = flytekit.current_context().execution_id
    new_df = pd.DataFrame.from_dict(
        {
            **{
                "model": [model],
                "project": execution_id.project,
                "domain": execution_id.domain,
                "timestamp": str(pd.Timestamp.now()),
                "execution_name": execution_id.name,
            },
            **kwargs,
        }
    )
    if df is None:
        df = new_df
    else:
        df = pd.concat([df, new_df])
    
    df.set_index("model", inplace=True)

    # Save the dataframe to the results file
    df.to_csv(result_file.path)

    # Record the experiment and overwrite the results file.
    return FlyteFile(path=result_file.path, remote_path=result_file.remote_source), df



@task(cache=False)
def track_experiment_results(
    result_file: FlyteFile, model: str, accuracy: float
) -> Tuple[FlyteFile, Annotated[pd.DataFrame, TopFrameRenderer(10)]]:
    """
    This task tracks experimental results inside the result file. To use it, modify it's parameters to take the metrics that you want to track,
    and pass them into the private helper below.

    The results will be persisted on s3 and rendered in the flyte deck for this task.

    If you change the arguments to this task, it is a good idea to remove the existing results with:

    aws s3 rm s3://bv-ml-ops/pipelines/auto-decisions/reporting/experiment_results.csv
    """
    return _track_experiment_results(
        result_file=result_file, model=model, accuracy=accuracy
    )
