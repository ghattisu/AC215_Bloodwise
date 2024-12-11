"""
Module that contains the command line app.

Typical usage example from command line:
        python cli.py
"""

import os
import argparse
import random
import string
from kfp import dsl
from kfp import compiler
import google.cloud.aiplatform as aip
from model import model_training as model_training_job, model_deploy as model_deploy_job


GCP_PROJECT = os.environ["GCP_PROJECT"]
GCS_BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]
BUCKET_URI = f"gs://{GCS_BUCKET_NAME}"
PIPELINE_ROOT = f"{BUCKET_URI}/pipeline_root/root"
GCS_SERVICE_ACCOUNT = os.environ["GCS_SERVICE_ACCOUNT"]
GCS_PACKAGE_URI = os.environ["GCS_PACKAGE_URI"]
GCP_REGION = os.environ["GCP_REGION"]

# Read the docker tag file
with open(".docker-tag-ml") as f:
    tag = f.read()

tag = tag.strip()

print("Tag>>", tag, "<<")

#SCRAPING_IMAGE = f"gcr.io/{GCP_PROJECT}/bloodwise-ai-scraping:{tag}"
VECTOR_DB_IMAGE = f"gcr.io/{GCP_PROJECT}/bloodwise-ai-vector:{tag}"


def generate_uuid(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def data_processor():
    print("data_processor()")

    # Define a Container Component for data processor
    @dsl.container_component
    def vector_db_processing():
        container_spec = dsl.ContainerSpec(
            image=VECTOR_DB_IMAGE,
            command=[],
            args=[
                "cli.py",
                "--download",
                "--chunk",
                "--embed",
                "--load"
                f"--bucket {GCS_BUCKET_NAME}",
            ],
        )
        return container_spec

    # Define a Pipeline
    @dsl.pipeline
    def data_processor_pipeline():
        vector_db_processing()

    # Build yaml file for pipeline
    compiler.Compiler().compile(
        data_processor_pipeline, package_path="data_processor.yaml"
    )

    # Submit job to Vertex AI
    aip.init(project=GCP_PROJECT, staging_bucket=BUCKET_URI)

    job_id = generate_uuid()
    DISPLAY_NAME = "bloodwise-ai-vector-db-" + job_id
    job = aip.PipelineJob(
        display_name=DISPLAY_NAME,
        template_path="data_processor.yaml",
        pipeline_root=PIPELINE_ROOT,
        enable_caching=False,
    )

    job.run(service_account=GCS_SERVICE_ACCOUNT)


def model_deploy():
    print("model_deploy()")
    # Define a Pipeline
    @dsl.pipeline
    def model_deploy_pipeline():
        model_deploy(
            bucket_name=GCS_BUCKET_NAME,
        )

    # Build yaml file for pipeline
    compiler.Compiler().compile(
        model_deploy_pipeline, package_path="model_deploy.yaml"
    )

    # Submit job to Vertex AI
    aip.init(project=GCP_PROJECT, staging_bucket=BUCKET_URI)

    job_id = generate_uuid()
    DISPLAY_NAME = "bloodwise-ai-model-deploy-" + job_id
    job = aip.PipelineJob(
        display_name=DISPLAY_NAME,
        template_path="model_deploy.yaml",
        pipeline_root=PIPELINE_ROOT,
        enable_caching=False,
    )

    job.run(service_account=GCS_SERVICE_ACCOUNT)


def pipeline():
    print("pipeline()")

    # Define a Container Component for data processor
    @dsl.container_component
    def data_processor():
        container_spec = dsl.ContainerSpec(
            image=VECTOR_DB_IMAGE,
            command=[],
            args=[
                "cli.py",
                "--download",
                "--chunk",
                "--embed",
                "--load",
                f"--bucket {GCS_BUCKET_NAME}",
            ],
        )
        return container_spec

    # Define a Pipeline
    @dsl.pipeline
    def ml_pipeline():
        # Data Processor
        data_processor_task = (
            data_processor()
            .set_display_name("Data Processor")
        )
        # Model Deployment
        model_deploy_task = (
            model_deploy_job(
                bucket_name=GCS_BUCKET_NAME,
            )
            .set_display_name("Model Deploy")
            .after(data_processor_task)
        )

    # Build yaml file for pipeline
    compiler.Compiler().compile(ml_pipeline, package_path="pipeline.yaml")

    # Submit job to Vertex AI
    aip.init(project=GCP_PROJECT, staging_bucket=BUCKET_URI)

    job_id = generate_uuid()
    DISPLAY_NAME = "bloodwise-ai-pipeline-" + job_id
    job = aip.PipelineJob(
        display_name=DISPLAY_NAME,
        template_path="pipeline.yaml",
        pipeline_root=PIPELINE_ROOT,
        enable_caching=False,
    )

    job.run(service_account=GCS_SERVICE_ACCOUNT)


def main(args=None):
    print("CLI Arguments:", args)

    if args.data_processor:
        print("Data Processor")
        data_processor()

    if args.model_deploy:
        print("Model Deploy")
        model_deploy()

    if args.pipeline:
        pipeline()


if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal 'python cli.py --help', it will provide the description
    parser = argparse.ArgumentParser(description="Workflow CLI")

    parser.add_argument(
        "--data_processor",
        action="store_true",
        help="Run just the Data Processor for Vector DB Instantiation",
    )
    parser.add_argument(
        "--model_deploy",
        action="store_true",
        help="Run just Model Deployment",
    )
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="Bloodwise AI Pipeline",
    )

    args = parser.parse_args()

    main(args)