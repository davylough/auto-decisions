from flytekit import task

from src.tasks.hello import get_hello_message


@task
def say_hello() -> str:
    message = get_hello_message()
    print(message)
    return message
