# Data Versioning using DVC
In this project, we use DVC as our data versioning tool. Everything will be run inside containers using Docker.

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
        |-fine-tuning-sg
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
We will be using [DVC](https://dvc.org/) as our data versioning tool. DVC (Data Version Control) is an open-source, Git-based data science tool. It applies version control to your data, make your repo the backbone of your project.

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
* We then mount the "images" folder in the bucket mount to the "/app/dataset" folder

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
`dvc add dataset`

#### Push to Remote Registry
`dvc push`

You can go to your GCS Bucket folder `dvs_store` to view the tracking files

## Docker Cleanup
To make sure we do not have any running containers and clear up an unused images
* Run `docker container ls`
* Stop any container that is running
* Run `docker system prune`
* Run `docker image ls`
