# Data Versioning using DVC
- For data reproducibility and storage efficiency, data versioning is essential in machine learning and data science projects. We will be using [DVC](https://dvc.org/) as our data versioning tool. DVC (Data Version Control) is an open-source, Git-based tool that integrates seamlessly with Git, which is why we chose DVC for data versioning.
- Everything will be run inside containers using Docker.

## Prerequisites
* Have tha latest Docker installed

## Make sure we do not have any running containers and clear up an unused images
* Run `docker container ls`
* Stop any container that is running
* Run `docker system prune`
* Run `docker image ls`

### Clone the github repository
* Cloned  repository from [here](https://github.com/ghattisu/AC215_Bloodwise.git) to your local machine 

Your folder structure should look like:
```
    |-AC215_Bloodwise
        |-llm
        |-fine-tuning
        |-scraping
        |-dvc
        |-secrets
```

### Setup GCP Service Account
- To set up a service account, go to the [GCP Console](https://console.cloud.google.com/home/dashboard), search for "Service accounts" in the top search box, or navigate to "IAM & Admin" > "Service accounts" from the top-left menu. 
- Create a new service account called "blooswise-data-versioning" 
- In "Grant this service account access to project" select:
    - Storage Admin
- This will create a service account.
- Click the service account and navigate to the tab "KEYS"
- Click the button "ADD Key (Create New Key)" and Select "JSON". This will download a private key JSON file to your computer. 
- Copy this JSON file into the **secrets** folder and rename it to `data-versioning.json`.

Download the json file and place inside the secrets folder:
<a href="https://console.cloud.google.com/iam-admin/serviceaccounts?project=bloodwise-ai" download>data-versioning.json</a>


### Create a Data Store folder in GCS Bucket
- Go to `https://console.cloud.google.com/storage/browser`
- Go to the bucket `blooswise-data-versioning` 
- Create a folder `dvc_store` inside the bucket
- Create a folder `images` inside the bucket (This is where we will store the images that need to be versioned)

## Run DVC Container

### Setup DVC Container Parameters
In order for the DVC container to connect to our GCS Bucket open the file `docker-shell.sh` and edit some of the values to match your setup
```
export GCS_BUCKET_NAME="blooswise-data-versioning"
export GCP_PROJECT="bloodwise-ai"
export GCP_ZONE="us-central1-a"
```
### Note: Addition of `docker-entrypoint.sh`
Note that we have added a new file called `docker-entrypoint.sh` to our development flow. A `docker-entrypoint.sh` is used to simplify some task when running containers such as:
* Helps with Initialization and Setup: 
   * The entrypoint file is used to perform necessary setup tasks when the container starts. 
   * It is a way to ensure that certain operations occur every time the container runs, regardless of the command used to start it.
* Helps with Dynamic Configuration:
   * It allows for dynamic configuration of the container environment based on runtime variables or mounted volumes. 
   * This is more flexible than hardcoding everything into the Dockerfile.

For this container we need to:
* Mount a GCS bucket to a volume mount in the container

### Run `docker-shell.sh`
- Make sure you are inside the `dvc` folder and open a terminal at this location
- Run `sh docker-shell.sh`  


### Version Data using DVC
In this step we will start tracking the dataset using DVC

#### Initialize Data Registry
In this step we create a data registry using DVC
`dvc init`

#### Add Remote Registry to GCS Bucket (For Data)
`dvc remote add -d dataset gs://blooswise-data-versioning/dvc_store`

#### Add the dataset to registry
`dvc add datasets`

#### Push to Remote Registry
`dvc push`

You can go to your GCS Bucket folder `dvs_store` to view the tracking files


#### Update Git to track DVC 
Run this outside the container. 
- First run git status `git status`
- Add changes `git add .`
- Commit changes `git commit -m '...'`
- Add a dataset tag `git tag -a 'dataset_v1' -m 'tag dataset'`
- Push changes to github
- Push tag to github `git push --tags`

## Make changes to data

### Upload new dataset from local

#### Add the dataset (changes) to registry
`dvc add datasets`

#### Push to Remote Registry
`dvc push`

#### Update Git to track DVC changes (again remember this should be done outside the container)
- First run git status `git status`
- Add changes `git add .`
- Commit changes `git commit -m '...'`
- Add a dataset tag `git tag -a 'dataset_v2' -m 'tag dataset'`
- Push changes to github
- Push tag to github `git push --tags`


### Get (different version) data using DVC 
Run this inside the container 
- To get the most recent version of the data, run `dvc get https://github.com/ghattisu/AC215_Bloodwise.git dvc/datasets --rev milestone2`
Your folder structure should look like:
```
    |-datasets
        |-input-datasets
        |-llm-finetune-dataset
```
Inside the dvc folder, it will create a new datasets that contains input dataset for both LLM and Fine-tuning


- To get the specific version (previous version) of the data, run `dvc get https://github.com/ghattisu/AC215_Bloodwise.git dvc/datasets --force --quiet --rev dataset_v1`
Your folder structure should look like:
```
    |-datasets
        |-input-datasets

```
Inside the dvc folder, it will create a new datasets that contains only the input dataset for LLM 


#### Caution!
Everytime before you run `dvc get https://github.com/ghattisu/AC215_Bloodwise.git dvc/datasets --force --quiet --rev milestone2` or `dvc get https://github.com/ghattisu/AC215_Bloodwise.git dvc/datasets --rev milestone2`, please ensure that datasets folder does not exist!


#### Troubleshooting
When you enter `dvc get https://github.com/ghattisu/AC215_Bloodwise.git dvc/datasets --rev milestone2`, you will be asked to enter your github username and password. If you get the following error: 
```
‘ERROR: failed to get 'dvc/datasets' - SCM error: Failed to clone repo 'https://github.com/ghattisu/AC215_Bloodwise.git' to '/tmp/tmpg0rguocjdvc-clone': No valid credentials provided’
```
Go to [Adding a new SSH key to your GitHub account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account?platform=mac) to set up your personal token. After successfully setup your personal token, use that private key as your github password.


## Docker Cleanup
To make sure we do not have any running containers and clear up an unused images
* Run `docker container ls`
* Stop any container that is running
* Run `docker system prune`
* Run `docker image ls`
