import datetime

import pandas
from flytekit import SQLTask, TaskMetadata, kwtypes, task, workflow
from flytekit.testing import patch, task_mock
from flytekit.types.schema import FlyteSchema

"""
    Mockable task
"""
query = """SELECT *
        FROM hive.city.fact_airport_sessions
        WHERE ds = 'test' LIMIT 10
        """
sql = SQLTask(
    "my-query",
    query_template=query,
    inputs=kwtypes(ds=datetime.datetime),
    outputs=kwtypes(results=FlyteSchema),
    metadata=TaskMetadata(retries=2),
)

"""
    Typically the following task and workflow will be in stored in src
    but is here to demonstrate flyte's mock capabilities
"""


@task
def t1() -> datetime.datetime:
    return datetime.datetime.now()


@workflow
def my_wf() -> FlyteSchema:
    dt = t1()
    return sql(ds=dt)


"""
    The task_mock construct returns a MagicMock object than can be overridden
"""
def test_mock():
    with task_mock(sql) as mock:
        mock.return_value = pandas.DataFrame(data={"x": [1, 2], "y": ["3", "4"]})
        assert (
            (
                    my_wf().open().all()
                    == pandas.DataFrame(data={"x": [1, 2], "y": ["3", "4"]})
            )
                .all()
                .all()
        )


"""
    Patch offers the same functionality, but in the Python patching style,
    where the first argument is the MagicMock object.
"""
@patch(sql)
def test_patch(mock_sql):
    mock_sql.return_value = pandas.DataFrame(data={"x": [1, 2], "y": ["3", "4"]})
    assert (
        (my_wf().open().all() == pandas.DataFrame(data={"x": [1, 2], "y": ["3", "4"]}))
            .all()
            .all()
    )
