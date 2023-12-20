from kedro.pipeline import node, Pipeline
from cms_auto_approval.pipelines.data_science_mumford_data.nodes import (
    train_model
)

def create_pipeline(**kwargs):
    return Pipeline(
        [
            node(
                func=train_model,
                inputs="primary_mumford_candidates_local",
                outputs="model_local",
                name="train_model"
            )
        ]
    )