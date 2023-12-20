from kedro.pipeline import node, Pipeline
from cms_auto_approval.pipelines.data_engineering_mumford_data.nodes import (
    preprocess_mumford_data
)

def create_pipeline(**kwargs):
    return Pipeline(
        [
            node(
                func=preprocess_mumford_data,
                inputs="mumford_candidate_data_raw_local",
                outputs="primary_mumford_candidates_local",
                name="preprocess_mumford_data"
            )
        ]
    )