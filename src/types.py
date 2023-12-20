import pandas as pd
from flytekit import HashMethod
from hashable_df import hashable_df
from typing_extensions import Annotated


def _hash_pandas_dataframe_function(df: pd.DataFrame) -> str:
    # We use hashable_df here to deal with lists in the dataframe to be hashed
    # Otherwise it throws an error stating "TypeError: unhashable type: 'list'"
    return str(pd.util.hash_pandas_object(hashable_df(df)))

"""
Use this type if you are returning pandas data frames and want the results to be cached.
See https://docs.flyte.org/projects/cookbook/en/stable/auto/core/flyte_basics/task_cache.html#caching-of-non-flyte-offloaded-objects for more info.
Example usage:

from src.types import CachedDataFrame

@task(cache=True, cache_version="1.0")
def my_task() -> CachedDataFrame:
    ....
"""
CachedDataFrame = Annotated[
    pd.DataFrame, HashMethod(_hash_pandas_dataframe_function)  # noqa: F821
]
