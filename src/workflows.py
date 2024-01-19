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
def my_wf():
    
    res = run_package()

    return res
 

if __name__ == "__main__":
    print(f"Running my_wf() {my_wf()}")
