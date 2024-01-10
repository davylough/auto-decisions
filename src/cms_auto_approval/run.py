
"""Application entry point."""
from pathlib import Path

from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession


def run_package():
    # Entry point for running a Kedro project packaged with `kedro package`
    # using `python -m <project_package>.run` command.
    print("yeet1")
    package_name = Path(__file__).resolve().parent.name
    print("yeet2")
    configure_project(package_name)
    print("yeet3")
    with KedroSession.create(package_name) as session:
        print("yeet4")
        session.run()


if __name__ == "__main__":
    run_package()
