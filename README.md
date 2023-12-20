# auto-decisions

Workflow scripts are in `src/`. 

## Getting Started

### Prerequisites

- Docker
- Python 3.11.6
- Flyte Configured (`~/.flyte/config.yaml` should exist)

If you are completely new to Flyte, create the initial `config.yaml` with:
```
brew install flytectl
flytectl config init --host https://flyteconsole.us-east-1.prod.internal.curalate.com
```

### Python Virtual Environment 
Create the virtual environment & install the requirements:
```
export CODEARTIFACT_AUTH_TOKEN=$(aws --profile ml-platform-curalate-prod --region us-east-1 codeartifact get-authorization-token --domain curalate-ml --domain-owner 492572841545 --query authorizationToken --output text)
pipenv install --dev
```
Enter virtual environment:
```
pipenv shell
```

### Project Setup

If this is a completely new project, you'll need to initialize the flyte project and ecr repo:
```sh
make init
```

## Working On This Project

### Running A Workflow
A `run` script is provided for your convinience. It takes the parameters `workflows.py` and the name of your workflow to run.

So, for example:
```sh
./run src/workflows.py my_wf
```
will run the workflow included in this template.

In order to run a Flyte workflow locally, your AWS config should have the `ml-platform-curalate-prod` sentry2 profile. Follow [this](https://bazaarvoice.atlassian.net/wiki/spaces/DEV/pages/78185693189/Machine+Learning+Sentry2+Access) documentation to set it up. Note that the `aws sso login` command requires AWS CLI v2.

### Running Tests
To run unit tests:
```sh
make test
```

### Code Style

Black and flake8 can be run with:
```sh
make code_style
```

### Running Remotely
You may want to run your code remotely on the qa cluster before making a pull request. This is a common useflow when you need more resources or have a long-running task. 

Do to this, first check in your changes:
```sh
git commit -a -m "My local changes...."
```
and then run:
```sh
./run --remote src/workflows.py my_wf
```


A bit about what's happening behind the scenes here:
* `./run` is going to call `make runcmd` in this case, which will build your container and push it to ecr.
* The version of your docker container and flyte project will be set to `dev-GIT_SHORTHASH`. This will ensure reproducibility, but requires you to check your code into git locally before calling.


**Please** see the [Building Data Pipelines](https://bazaarvoice.atlassian.net/wiki/spaces/DEV/pages/78087192634/MLOps+Step+2+Data+Preparation#Building-Data-Pipelines) documentation for more info on how Flyte works and more about this workflow.

## Make Targets

The `Makefile` has a number of other targets you may find useful (or are used by Jenkins):
* `info` shows the current info about the project and any registered launchplans in flyte.
* `init` sets up ECR and flyte for this project -- should only be run once after the template is created.
* `build` builds the docker container and inject the code in the `src` directory into it. (Note: You _must_ check your code into git before running this.)
* `push` pushes the docker container to ecr
* `package` creates the protobuf files for this workflow to send to the remote flyte cluster
* `register` registers this project with flyte
* `test` runs unit tests
* `code_style` runs autoformatting and the linter
* `promote` registers this project in the `prod` domain (Note: you shouldn't use this -- Jenkins should upon release)
* `runcmd` is a helper to `run` -- it ensures the current code is in ECR and flyte so you can use `./run --remote` (see [Building Data Pipelines](https://bazaarvoice.atlassian.net/wiki/spaces/DEV/pages/78087192634/MLOps+Step+2+Data+Preparation#Building-Data-Pipelines) for more info.) 


## Jenkinsfile (V3 Services)
While the cookiecutter creates a directory to quickly start writiing a flyte workflow,
you still need to add the following in your `Jenkinsfile` for CI/CD to build/push the 
workflow automatically

Changes needed:
- Before your `utils.build { BuildMetadata data ->`
```
def flyteWorkflows = ['auto-decisions']
```
- Before your `if (data.hasCodeChange) {` & after `utils.build { BuildMetadata data ->`
```
setBuildParameters(flyteWorkflows)
setBuildName(version)
```
- As a stage after `generateAndDeployJouleJobs(service, aws.region.US_EAST_1, "prod")`
```
stage('Build Flyte Components') {
    flyteWorkflows.each { dir ->
        if (hasCodeChangedInDirectory(dir, utils, data)) {
            buildFlyteWorkflow(dir, "133-133-fbc2907", data)
        }
    }
}
```
- Last line of pipeline build
```
setBuildParameters(flyteWorkflows)
```
