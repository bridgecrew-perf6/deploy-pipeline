# Deploy Pipeline

This is a set of scripts to dynamically create a staged Gitlab pipeline to support automated deployments from Gitlab.
You can think of it as a wrapper around a `.gitlab-ci.yml` file.  By supplying a template (simply a properly formatted 
yaml file) as well as a set of host and package configuration files, the output of the script will be a pipeline
file that can be passed to the `trigger` command and executed as a [Dynamic Child Pipeline](https://docs.gitlab.com/ee/ci/parent_child_pipelines.html#dynamic-child-pipelines).
