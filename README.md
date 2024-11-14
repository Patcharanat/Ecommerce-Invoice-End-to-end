# End-to-end E-commerce Data Project - AI-Driven Interpretable Dynamic Customer Segmentation
*Patcharanat P.*
```text
Click "⋮≡" at top right to show the table of contents.
```
**End-to-end Data project** in the e-commerce and retail industries covering the full process of data exploitation, including Data Engineering skills, Data Science skills, and Data Analytic skills, and how to automate ML lifecycle management (MLOps).

***Disclaimer**: This documentation not only focused on outcomes, but also explained concepts and details for reproduction*

## **Context**

It's crucial in nowadays to emphasize data existing and make the most use of it. **The project was created to practice and demonstrate the full process of data exploitation** covering setting up environments, ETL process, Web Scraping, Data Visualization, Machine Learning Model Development, and Model Deployment using E-commerce data.

## **Table of Contents**:
*(latest revised: July 2023, Aug 2023, Oct 2024, Nov 2024)*
1. [Setting up Environment](#1-setting-up-environment)
    - 1.1 [Setting up Overall Services (containers)](#11-setting-up-overall-services-containers)
2. [ETL (Extract, Transform, Load): Writing DAGs and Managing Cloud Services](#2-etl-process-writing-dags-and-managing-cloud-services)
    - 2.1 [Setting up Data Lake, and Data Warehouse](#21-setting-up-data-lake-and-data-warehouse)
        - [**Terraform**](#terraform)
    - 2.2 [Setting up DAG and Connections](#22-setting-up-dag-and-connections)
    - 2.3 [Triggering DAG and Monitoring](#23-triggering-dag-and-monitoring)
    - [Step to Reproduce Virtualization for Testing](#step-to-reproduce-virtualization-for-testing)
    - 2.4 [Extending to AWS](#24-extend-to-aws)
        - [Terraform for AWS](#terraform-for-aws)
    - 2.5 [Detail of the ETL Code](#25-detail-of-the-etl-code)
    - 2.6 [**Airflow DAGs and Data warehouse in Production**](#26-airflow-dags-and-data-warehouse-in-production)
<!-- 3. [Web Scraping](#3-web-scraping) -->
3. Web Scraping
4. [EDA and Data Visualization](#4-eda-and-data-visualization)
    - 4.1 [EDA](#41-eda)
    - 4.2 [PowerBI Dashboard](#42-powerbi-dashboard)
    - 4.3 [**Data Modeling and Optimization in Production**](#43-data-modeling-and-optimization-in-production)
        - [How to Optimize Data Models](#how-to-optimize-data-models)
5. [Machine Learning Model Development](#5-machine-learning-model-development)
    - 5.1 [Customer Segmentation By RFM, KMeans, and Tree-based Model](#51-customer-segmentation-by-rfm-kmeans-and-tree-based-model)
    - 5.2 [Market Basket Analysis](#52-market-basket-analysis)
    - 5.3 [Demand Forecasting](#53-demand-forecasting)
    - 5.4 Recommendation System
    - 5.5 Customer Churn Prediction
    - 5.6 Price Analysis and Optimization
    <!-- - 5.4 [Recommendation System](#54-recommendation-system) -->
    <!-- - 5.5 [Customer Churn Prediction](#55-customer-churn-prediction) -->
    <!-- - 5.6 [Price Analysis and Optimization](#56-price-analysis-and-optimization) -->
6. [ML Code Productionization and Deployment](#6-ml-code-productionization-and-deployment)
    - 6.1 [Exporting from Notebook](#61-exporting-from-notebook)
    - 6.2 [Docker Containerization](#62-docker-containerization)
    - 6.3 [Deploying the Model to the Cloud Environment](#63-deploying-the-model-to-the-cloud-environment)
    - 6.4 [CI/CD Workflow - Automated Deployment Process](#64-cicd-workflow-automated-deployment-process)
7. [Conclusion](#7-conclusion)

*Disclaimer: The project is not fully finished, but covered all the parts available as links above.*

## **Project Overview**

![project-overview](./src/Picture/project-overview.png)

## **Tools**:
- Sources
    - Postgres Database (Data warehouse)
    - REST API (raw file url)
    - API (with token)
- Data Lake & Staging Area
    - Google Cloud Storage
    - AWS S3
    *(Extend to Azure Blob Storage in the future)*
- Data Warehouse
    - Postgres Database
    - Bigquery (External and Native Tables)
    - Redshift
    *(Extend to Azure Synapse in the future)*
- Orchestrator
    - Airflow
- Virtualization and Infrastucture management
    - Docker compose
    - Terraform
- EDA & Visualization
    - PowerBI (Desktop and Service)
    - Python (Jupyter Notebook)
- Machine Learning Model Development
    - Jupyter Notebook
- Model Deployment and Monitoring
    - FastAPI (Model Deployment)
    - ~~Streamlit (Monitoring)~~
    - Artifact Registry
    - Cloud Run
    - Github Actions (CI/CD)

Dataset: [E-Commerce Data - Kaggle](https://www.kaggle.com/datasets/carrie1/ecommerce-data)

## Prerequisites:
- Get a credentials file from kaggle and activate the token for API.
- Have Google Account being able to use google cloud services.
- Docker Desktop
- Python

*Although `.env` file is push to the repository, sensitive data and the credentials are hidden in by `.gitignore`*

## 1. Setting up Environment

![setting-overview](./src/Picture/setting-overview.png)

Firstly, clone this repository to obtain all neccessary files, then use it as root working directory.
```bash
git clone https://github.com/Patcharanat/ecommerce-invoice
```
We need to set up local environment with docker to perform ETL process, which basically including:
- Postgres database
- Airflow

Since the pipelines might need to be run in different environment not just on your machine, it's essential to make sure that your code can be packaged and run in anywhere or orchestrated by different tools for further scaling up. Developing and testing your code to perform ETL/ELT processes in a **Docker** container is essential. **Docker Compose** make it possible to do it, orchestraing multiple containers (and maybe built by different images) with a lightweight approach simulating running on different environment. 

Usually, we don't use docker compose in production, but it is lightweight and easy enough to enable you to run and test your code on local machine. However, packing your code as a docker image is still the way to go for production scale pipeline, specifically for *Kubernetes* as an example.

### 1.1 Setting up Overall Services (containers)

Open your docker desktop and execute bash command in terminal with your root working directory (in a clone repo) by:

```bash
docker compose build
```

This command will build all containers we specified in [docker-compose.yml](./docker-compose.yml) file, especially in `build` and `context` parts which do following tasks:
- Copying [setup.sql](./setup.sql) script to `docker-entrypoint-initdb.d` path in a container to be executed when we initialize the session.
- Copying [cleaned_data.csv](./data/cleaned_data.csv) file to the postgres container as an mock-up source database.
- Creating schema and table with `cleaned_data.csv` by executing `setup.sql` within the container.
- Replicating postgres container to simulate another database for data warehouse with empty table using `postgres-target.Dockerfile`, and `target.sql` file.
- Installing `requirements.txt` for airflow's container to be able to use libraries we needed in DAGs.
- Add a Kaggle credentials file: `kaggle.json` (in this case we use Kaggle API) to make API usable.

**Note**
- `docker compose build` is creating container(s), following specification within `Dockerfile` file type specified in `docker-compose.yml` of how it should be built, in your local machine, but it's still not spinning up.

**Debugging Note**
- you may fail to run the command because you may not have google cloud credentials as a json file in your local. You can skip to [Step 2.1: Setting up Data Lake, and Data Warehouse](#step-21-setting-data-lake-and-data-warehouse) in ***Service account*** part to get your own google crendentials json file and put it in `credentials` folder. After that you can try running `docker compose build` again.
- Don't forget to get `Kaggle.json` credentials, and add to `credentials` folder also.

**Reproducing Note**
- First, you need to simulate postgres database by creating a container with postgres image. you will need to copy `cleaned_data.csv` file into the postgres container. Then, you need to create a database and a schema, and a table with [`setup.sql`](setup.sql) file, and also configure [`.env`](.env) file, like username, password, and database. The file that will do the copying file task is [`postgres.Dockerfile`](postgres.Dockerfile)
- We added another postgres container to simulate target database. The files that are relevant to this task are [`postgres-target.Dockerfile`](postgres-target.Dockerfile) to build image for the container and [`target.sql`](target.sql) to setup empty table. In this database, we will use different database name and different schema for testing how to handle with multiple databases.
- Then, you need to create a container with airflow image. You will need to copy `kaggle.json` file into the container (webserver, and scheduler). Then, you need to install libraries we needed in DAGs by **"pip install"**[`requirements.txt`](requirements.txt) file within the containers. The file that will do the task is [`airflow.Dockerfile`](airflow.Dockerfile)
- Then, you need to create a container with airflow image. You will need to copy `kaggle.json` file into the container (webserver, and scheduler). Then, you need to install python dependencies we needed in DAGs by `pip install -r`[`requirements.txt`](requirements.txt) file within the containers. The file that will do the task is [`airflow.Dockerfile`](airflow.Dockerfile)
- To easily run multiple docker containers or running microservices, you will need docker compose. The file that will do the task is [`docker-compose.yml`](docker-compose.yml), which will `build` all the images for containers we specified in `build` and `context` parts resulting in running different `.Dockerfile` for different containers.

In airflow official site, you will find [`docker-compose.yml`](https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml) template to run airflow you can use it as reference and change it to fit your needs, like adding postgres section, and remove unnecessary part that can causes running out of memory making you unable to run docker containers successfully.

If you're new to container, you will be confused a little with using path. please be careful with paths where you mount the files to.

### 1.2 Intializing all Containers
Initialize docker container(s) and run process in background (Detach mode)

```bash
docker compose up -d
```

***Note:** some services need time to start, check container's logs from **docker desktop UI** or `docker ps` to see if the services are ready to work with.*

<img src="./src/Picture/docker-ps.jpg">

### 1.3 Checking if all Dockerfiles correctly executed
What's needed to be checked are
- Is the data table in postgres database as a source created correctly?
    - data loaded from `cleaned_data.csv` and using the right schema?
- Is all the credentials file imported?
    - `kaggle.json`
    - `gcs_credentials.json`
    - `ecomm-invoice-kde-aws-iam_accessKeys.csv`
- Is the data table in postgres database as a target created correctly?
    - empty table with the right schema?

Getting into terminal of the container we specified by:
```bash
docker exec -it <container-name-or-id> bash
```

*Note: You can get container's name or id from `docker-compose.yml` or from `docker ps` command.*

At this step, we can check if csv file we meant to execute in Dockerfile is executed successfully by:
```bash
ls
ls data/
ls docker-entrypoint-initdb.d/
```

you should see the data csv file and `setup.sql` file in the directory.

<img src="./src/Picture/dockerfile-executed.jpg">

What you should check more is that credentials file: `kaggle.json` correctly imported in airflow's scheduler and webservice containers.

### 1.4 Checking Data in a Database
Access to both postgres containers, and then access database to check if csv file copied into table.
```bash
psql -U postgres -d mydatabase
```
Then we will be mounted into postgres' bash

Then we will check table, and schema we executed by `setup.sql` file
```bash
\dt or \d -- to see tables list
\dn or \z -- to see schemas list
```
if we see table and schema are corrected and shown, then importing csv to the Postgres database part is done.

<img src="./src/Picture/check-postgres.jpg">

if not, these can be issues
- check if `setup.sql` is executed successfully, by inspecting logs in docker desktop
- check if data csv file and `setup.sql` are copied into docker container's local by using container's bash and check if path in `Dockerfile` and `setup.sql` were set correctly.
- we need to set search_path by
```bash
SET search_path TO <myschema>;
```
to set only in current session. *(reccomended)*
```bash
ALTER DATABASE <mydatabase> SET search_path TO <myschema>; 
```
to set permanently at database level.

In postgres bash, we will be able to see only the table that match the schema we created. Hence, we have to change the schema to see the table in the database.

Then exit from all bash
```bash
\q
exit
```

***Note:** In my lastest update adding another postgres databse to simulate data warehouse, I found that specifying image name in `docker-compose.ymal` file is crucial when we pulling the same image but using in different container, because it will `build` with the wrong `Dockerfile` and cause the some issues, like build postgres database target with `postgres.Dockerfile` instead of `postgres-target.Dockerfile` which is not what we want.*

### 1.5 Exiting
Don't forget to remove all image and containers when you're done.
```bash
docker compose down -v
```

and remove all images via `docker desktop`, we will initiate `docker compose build` and `docker compose up -d` again, when we want to test developed ETL code (test our airflow DAGs).

<img src="./src/Picture/docker-desktop.jpg">

### 1.6 Setting up Airflow Web UI

To set up airflow, we need to define more 4 services that refer to [official's .yml file template](https://airflow.apache.org/docs/apache-airflow/2.6.1/docker-compose.yaml) including `airflow-postgres` to be backendDB, `airflow-scheduler` to make scheduler, `airflow-webserver` to make airflow accessible via web UI, and `airflow-init` to initiate airflow session.

<img src="./src/Picture/airflow-ui.jpg" width="75%">

Understanding how every components in `docker-compose.yml` work make much more easier to comprehend and debug issues that occur, such as `depends-on`, `environment`, `healthcheck`, `context`, `build`, and storing object in `&variable`.

***Note:*** In `yaml` file, identation is very important.

**For this project**, we create 3 postgres containers, so we need to check carefully if airflow connected to its own backendDB or the right database.

<details><summary>Issue debugged: for being unable to connect to airflow backendDB</summary>
<p>
Use this template from official's document in `.env` file:

```python
postgresql+psycopg2://<user>:<password>@<host>/<db>

#or

[dialect]+[driver]://[username:password]@[host:port]/[database]

# which results in

AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@airflow-postgres/airflow
```

</p>
</details>

***Note:*** In `.env` file, airflow core need *FERNET* key which can be obtained from fernet.py (randomly generated)

## 2. ETL process: Writing DAGs and Managing Cloud Services

In this project, I used a dataset from kaggle which was:
- loaded to postgres database
- uploaded to this repo github as csv format
- and I wrote DAGs to use Kaggle API to obtain the dataset directly from the Kaggle website.

<img src="./src/Picture/etl-overview.png">

If you use different dataset, you might have to write your own DAGs what match your specific use cases.

### 2.1 Setting up Data Lake, and Data Warehouse
As we will use GCP (Google Cloud Platform) for  Data Lake and Data Warehouse, we need to make our airflow script, which run in docker containers locally, being able to connect to GCP by using **google credentials** as known as a `service account` got from `IAM` section.

**Service Account**

Please follow this guideline:
1. Go to your GCP project console with available access to manage cloud resources, and go to navigation menu (3-bar icon at top left), then go to `IAM & Admin` > `Service Accounts` > `Create Service Account` > Create your Service Account 
2. In Service accounts section, click 3 dots at your newly created service account > `Manage keys` > `Add key` > `Create new key` > `JSON` > `Create` > `Download JSON` > `Close`, please keep your credentials (this json file) in safe place (must not be uploaded to anywhere public).
3. You have to to specify the permission that you allow for that service account, like how much it can manage resources. What you need to do is:
- Go to `IAM` page in `IAM & Admin` section > Edit principal for your created service account > Add Roles
- Add the following roles:
    - BigQuery Admin
    - Storage Admin
- And then, save your changes.

***Caution**: if you want to add your project to github, make sure you are working in private repo, or add it to `.gitignore` file*

Until now, you've finished getting service account credentials.

![gcp-iam](./src/Picture/gcp-iam.png)

**Data Lake**

The next step is creating your Google cloud storage bucket. Go to `Cloud Storage` > `Create` > `Name your bucket` (which is *globally unique*)

Then, choose the options that match you specific needs, the recommend are:
- `Location type`: Region
- `Storage Class`: Standard
- Activate `Enforce public access prevention`
- `Access control`: Uniform
- `Protection tools`: None

Click `Create`, and now you have your own data lake bucket.

<img src="./src/Picture/gcs-ui.jpg" width="75%">

**Data Warehouse**

The last step is creating your Bigquery dataset and table. In Bigquery (Google Data warehouse) you could have many projects, each project might have many datasets (most called *schema* for other OLAP databases), and each dataset might have many tables.

Do the following to create your dataset and table:
- Go to `Bigquery` > Click on 3-dot after your project name > `Create dataset` > `Name your dataset` (which is *unique* within the project) > `Create dataset`

*(Recommend to choose location type that suit your region)*

- Click on 3-dot after your created dataset > `Create table` > `Select your data source` (In this case, select empty table) > `name your table` > define schema > `Create table`

Until now, you've finished creating your data warehouse that's ready to load our data in.

<img src="./src/Picture/bigquery-ui.jpg" width="75%">

As you can see it's quite inconvenient that we have to create all of these resources manually via Google UI. So, we will use **Terraform** to create these resources in the next step.

#### **Terraform**

We can achieve creating the bucket, the dataset or table by **"Terraform"**, which is a better way to manage cloud resources reducing error-prone when reproducing the process. It's also proper for production stage with some additional concepts, we will discuss more on that later. you can see the code in `terraform` folder, consists of [main.tf](terraform/main.tf) and [variables.tf](terraform/variables.tf). Terraform make it easier to create, track stage, and delete the resources. In this demonstration, we enable it with a few bash commands.

The [`main.tf`](./terraform/main.tf) file, using some variables from [`variables.tf`](./terraform/variables.tf) file, will produce the following resources:
- 1 data lake bucket
- 1 Bigquery dataset
- 1 Bigquery table

To use terraform, you need to install Terraform in your local machine (+add to PATH), and have your google credentials (service account credentials) as a json file within `credentials` directory located in the same level of your root working directory. Then, you can run terraform commands in your terminal **in your terraform working directory**.

```bash
# workdir: terraform/
terraform init

terraform plan

terraform apply

terraform destroy
```

- `terraform init` initialize Terraform (where `main.tf` located) in your local machine (don't forget to `cd` into terraform directory first).
- `terraform plan` to see what resources will be created and syntax checking.
- `terraform apply` to create the resources.
- `terraform destroy` to delete the resources.

After all, you can see the result in your GCP console, in Google cloud storage, and Bigquery that it's already created bucket, dataset and an empty table together with newly created files in local filesystem such as `*.tfstate*`, and `.terraform*`. Please also add these files to `.gitignore` to avoid credential exposing.

***Note**: The written script made us easily create and **delete** the resources which proper for testing purpose not on production.*

### 2.2 Setting up DAG and Connections

<img src="./src/Picture/airflow-dag-graph.jpg">

In this project, I wrote main script: [`ecomm_invoice_etl_dag.py`](src/dags/ecomm_invoice_etl_dag.py) to create 1 DAG of **(8+1) tasks**, which are:
1. Reading data from raw url from github that I uploaded myself. Then, upload it to GCP bucket as uncleaned data.
2. Fetching (Unloading) data from the postgres database that we simulate in docker containers as a data source. Then, upload it to GCP bucket as cleaned data.
3. Downloading from the Kaggle website using Kaggle API. Then, upload it to GCP bucket (GCS) as uncleaned data. 
4. Data Transformation: reformat to parquet file, and cleaning data to be ready for data analyst and data scientist to use, then load to staging area.
5. Loading data located in staging area to data warehouse (Bigquery) as cleaned data with native table approach.
6. Loading to data warehouse (Bigquery) as cleaned data with external table approach from staging area.
7. Loading to another Postgres database as cleaned data.
8. Clearing data in staging area (GCP bucket). **(this will not be used for external table approach that requires the source file to be exists)**

Additionally, I also wrote [**transform_load.py**](./src/dags/transform_load.py) and [**alternative_cloud_etl.py**](./src/dags/alternative_cloud_etl.py) to demonstrate utilizing modularization or "utils" and how to use different cloud services, respectively.

After we wrote the DAG script, we're gonna test our DAG by initating docker compose again, and go to `localhost:8080` in web browser, trigger DAG and see if our DAG worked successfully.

But before triggering the DAG, we need to set up the connection between Airflow and our applications in Airflow web UI:

**Postgres connection**: Go to `Admin` > `Connections` > `Create` 
- `Connection Type:` **Postgres**
- `Host` *service name of postgres in docker-compose.yml*
- `Schema` *schema name we used in `setup.sql`*
- `Login` *username of postgres in docker-compose.yml*
- `Password` *username of postgres in docker-compose.yml*
- `Port` *username of postgres in docker-compose.yml*

<img src="./src/Picture/airflow-connections-postgres.jpg" width="75%">

And then, `Save`

***Note1:** we used **`database name`** that we specified in `docker-compose.yml` in DAG script where we need to connect to the database, PostgresHook with `conn_id` as Postgres Host name, and `schema` as **`database name`***.

***Note2:** we can omit `schema` argument in PostgresHook and Airflow connection, if we use `public` schema, or specify SELECT `myschema.table_name` FROM ... in `setup.sql`*

**Bigquery connection**: Go to `Admin` > `Connections` > `Create` 
- `Connection Id`: *your own defined name (will be use in DAG)*
- `Connection Type`: **Google Cloud** 
- `Project Id`: Your Project Id
- `Keyfile Path`: *absolute path to your service account credentials file*

<img src="./src/Picture/airflow-connections-google.jpg" width="75%">

And then, `Save` again.

**Note:** you have to change the code in [`ecomm_invoice_etl_dag.py`](src/dags/ecomm_invoice_etl_dag.py) to match your connection id that you created in Airflow UI, and your project id also.

For futher details, we only create connections of Postgres and Bigquery for fetching data from containerized Postgres database, and creating **external table** for Bigquery respectively because it's required, unless airflow could not connect to the applications and cause the bug. Most of time, you can tell if it requires connection in Airflow UI by existing of `conn_id` arguments in the Operators. But, the other connection,  like Google Cloud Storage, is not required to be created in Airflow UI, because we use the credentials file that mounted into Airflow container to authenticate the connection in the code.

<img src="./src/Picture/airflow-connections.jpg" width="75%">

<details><summary>Reproducing Note for DAGs development</summary>
<p>

- Reading direct from official documentation is a good way to develop your code and enable other team members easier to maintain, such as Google Cloud Documentation, and Kaggle API Documentation.
- Reading Logs after triggering DAG in airflow web UI was very helpful to debug the issues.
- When we have google credentials as a json file, it make us less concerned about how to authenticate, like gcloud, gsutil etc. (or even connection in Airflow). We just have to mount the credentials into the airflow container, put the path of the json file in the code and use the right API or library provided by provider which mostly can be found as templates in official documentation.
    - Although, this is not the best practice to manage your secret as mentioned in Terraform part.
- In order to handle python dependencies such as additional libraries to be available during runtime that are not belong to python default module, we have to add the additional lib to `requirements.txt` file, and install with `pip install -r` in custom airflow image, usally called baked image. And then, rebuild the image (`docker compose down -v`, `docker compose build`, `docker compose up -d`) again.
- Make sure we don't have any dependencies conflict and compatible with python version which can change in [airflow.Dockerfile](airflow.Dockerfile) by: 
```dockerfile
FROM apache/airflow:slim-2.6.2-python3.10
```
- I used `gcsfs` or `GCSFileSystem` in DAG script to run transformation task. the library allow us to manage and handle the data in GCS.
    - we also have to authenticate via `GCSFileSystem` instance in the code instead of `google.cloud.storage.Client`.
- When I first load the parquet file to pre-defined schema in Bigquery, I encountered the error that the schema is not matched. I found out that the schema of parquet file is not the same as the schema in Bigquery with extra column "index level 0". So, the solution is to drop the column before saving to parquet file in Google Cloud Storage by using `df.to_parquet(..., index=False)`, just like `to_csv('filename.csv', index=False)`.
    - *(Even you download the `index=True` parquet file to check in pandas, it will not show the extra index column)*
- *(Update)* Meanwhile I was developing other part of the project, a new airflow version(2.7) was launched, and the new version of airflow image is not compatible with the old version by airflow backendDB which caused a serious bug making `airflow-init` initialized unsuccessfully, `airflow-scheduler`, and `airflow-webserver` not work as expected.
    - the solution is to remove all containers, images, and existing volumes of airflow backendDB, and then intialize again with the fix image version.
        - remove local volumes by
        ```bash
        docker compose down --volumes --rmi all

        docker system prune --all --volumes
        ```
        - remove local airflow backendDB `postgres-db-volume`, and also `logs`, `plugins`, and `config` files in `src` folder.
    - I changed the airflow image version to `apache/airflow:2.6.2-python3.10` in [airflow.Dockerfile](airflow.Dockerfile) and `apache/airflow:2.6.2` in [docker-compose.yml](./docker-compose.yml) to the version of image.
    - Don't use the `latest` version in your script, if you want to make you work reproduceable.
</p>
</details>

**Bigquery: Native tables vs External tables**

<img src="./src/Picture/native-vs-external.png" width="75%">

In the DAG script, we have 2 tasks to load data to Bigquery, one is using Native table, and another is using External table. the differences between them are their performance and how it works.

External tables are suitable when you want to query data without loading it into BigQuery, optimizing storage costs and leveraging existing data sources. Native tables, on the other hand, offer enhanced performance and advanced features within BigQuery, like partitioning and clustering and more user-friendly.

### 2.3 Triggering DAG and Monitoring

After finishing the writing DAG part, we can go to `localhost:8080` via web browser and login with username, and password we defined in [docker-compose.yml](docker-compose.yml) file. Then, we can see the DAGs we created in the UI. We can trigger the DAG by clicking on the `Trigger DAG` button, and monitor the progress of the DAG by clicking on the DAG name.

You can also see the logs of each task by clicking on the task name in the DAG graph and see how the tasks flow is working via Graph.

<img src="./src/Picture/airflow-triggered.jpg">

Most of time, you don't write the DAGs in one time and test only once when it's done, you have to come to this UI, triggering and monitoring to see if it works or not, and then fix the bugs. It's very helpful to debug the code by reading the logs and checking which tasks are failed.

**Once the ETL DAG worked successfully, the data engineering part is finished.**

### **Step to Reproduce Virtualization for testing**
1. Apply Terraform to create the infrastructure
    ```hcl
    terraform plan

    terraform apply
    ```
2. Start microservices with docker-compose
    ```bash
    docker compose build

    docker compose up -d
    ```
3. Trigger the DAG in Airflow UI
    - go to `localhost:8080` via web browser
4. Check the data in Data Lake and Data Warehouse
    - login to Cloud Console
    - (If you want to test model deployment, you can do it here)
5. Stop microservices with docker-compose
    ```bash
    docker compose down -v
    ```
6. Destroy the infrastructure with Terraform
    ```hcl
    terraform destroy
    ```

### 2.4 Extending to AWS
In the previous part, I used GCP as a cloud service provider for data lake and data warehouse, but we can also use AWS (or Azure) as a cloud service provider. The process is quite similar to GCP, but it will have some differences in the code and architecture which we can adapt to it easily if we understand the concept of ETL.

We will use AWS **S3** as a data lake, and AWS **Redshift** as a data warehouse. As before, we need to create IAM user (which equal to service account in GCP) and get the credentials file as `.csv` extension, then use it to create S3 bucket and Redshift by **terraform**.

We will create an IAM user, and get the credentials file manually via Web IU. Access for AWS is quite more complex than GCP, composed of IAM user, IAM Role, and Policy which will not be described in detail in this project.

**IAM User and Policies**

To get the IAM user, we must have root user which is the first user we created when we created AWS account. Then,
- We need to go to `IAM` service in AWS console.
- And go to `Users` > `Add users` > Name an unique `User name` > `Attach existing policies directly`.
- Type in search box `AmazonS3FullAccess` and `AmazonRedshiftAllCommandsFullAccess` > check the box > `Create user`.
- Adding custom policies for Redshift Serverless by clicking the created user and then `Add permission` > `Create inline policy`,
    - use json option and type in this:
    ```json
    {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "iam:*",
                "ec2:*",
                "redshift-serverless:*"
            ],
            "Resource": "*"
        }
    ]
    }
    ```
    - `Next` > `Create policy`
- Get a csv credential file by clicking on the created user > `Security credentials` > `Create access key` > choose `Local Code` for our purpose > name an unique access key > `Download .csv file`

After getting the credentials file, mount it to your `credentials` folder. Now, we can use it in **terraform** to create S3 bucket and Redshift resources.

#### Terraform for AWS

In this part is quite complex due to **"static credentials"** behavior, since we don't need to hard-coded or type in the key derectly to the terraform file. So in general, we will use **"terraform.tfvars"** to pass the hard-coded credentials to terraform file and add `terraform.tfvars` to `.gitignore`.

The concept is simple: we create resources in `main.tf` where some part of it use `var.` to refer to the variable specified in `variables.tf` file. In `variables.tf` file, we specify the variable name, type, and default value, if the default value is not specified, we have to pass the value interactively after `terraform apply` as inputs **OR** pass it automatically by creating `terraform.tfvars` file and type in the variable name and value. This is where we will copy credentials from csv to put it in **(and again please don't forget to add both files to `.gitignore`)**.

All you need to do is creating `terraform.tfvars` (must be this name) in your `terraform` folder, and type in the following:
```hcl
# aws credentials
aws_access_key = "your-access-key"
aws_secret_key = "your-secret-key"

# optional for serverless redshift

# Application Definition
app_environment   = "dev" # Dev, Test, Staging, Prod, etc

# Network Configuration
redshift_serverless_vpc_cidr      = "10.0.0.0/16"
redshift_serverless_subnet_1_cidr = "10.0.1.0/24"
redshift_serverless_subnet_2_cidr = "10.0.2.0/24"
redshift_serverless_subnet_3_cidr = "10.0.3.0/24"
```

Then you good to go with `terraform apply`.

In Addition, configuring Redshift Serverless is quite complex, so I will not go into detail, but you can check the code in [main.tf](./terraform/main.tf). Basically we need to create the following:
- Data "aws_availability_zones" to get the availability zone.
- VPC
- Redshift subnet, and also config your available IP address in `terraform.tfvars`.
- IAM role for Redshift Serverless
- Grant some access and attach some policy for the role
- Workgroup
- Namespace

Unlike S3, which is much more easier to create, we just need to specify the name of the bucket, and the region.

*Note: Redshift Serverless let us create a data warehouse without managing the cluster ourselves, it can **scale down to zero** or **pay as you use**, but it's still in preview.*

### 2.5 Detail of the ETL Code

I intentionally separate the code for AWS and GCP, so we can easily find between them. The code for AWS is in [alternative_cloud_etl.py](./src/dags/alternative_cloud_etl.py) file. The code is quite similar to GCP, but there are some differences, such as:
- using `boto3` instead of `google.cloud.storage` to connect to S3.
- how we use credentials file to connect to the cloud.
- using `psycopg2` instead of `bigquery` to load to Redshift.
- uploading clean data to S3 bucket using `awswrangler`, which implemented on `pandas` library, instead of using `gcsfs`.
- how to fetch the data from postgres database to gcp and aws, which is different in the code, but the concept is the same.

**Note: Since we use the same file that is downloaded or fetched, so the deleting file from local airflow docker container will be deprecated avoiding conflict between clouds.** *Unless, it will cause a bug by `shutil` in the first run, because the file is not exists in the local container.*

*Note: Loading to Redshift part will be described more in the future*

### 2.6 Airflow DAGs and Data warehouse in Production
- **Airflow**
    - In the best practice, we wrap ETL processes into Airflow Opeators separately, can be either importing from official sites or sometimes customizing it to meet team's agreement or according to team's data governance.
    - Separating processes by multiple operators and written as the *OOP* pattern can represent DAGs, airflow jobs, or workflows in comprehensive way and make a task to be atomic and isolated from each other.
    - Most of time, official providers have their own developed operators associating with their products such as `GCSOperator`, `BigQueryOperator`, etc. that prevent us from error-proning developing it ourselves.
- **Data Warehouse**
    - This aspect can be vary across companies depended on data architecture design and data stack. However, there's quite a new term for modern data engineering called ***ELT*** pattern, which introduces a huge different from ETL. Basically, ELT allow us to adopt *[medallion architecture](https://www.databricks.com/glossary/medallion-architecture)*, separating processes into multiple data stages, keeping raw extracted data for later data reconciliation, and enabling fault-tolerant architecture by convenient backfilling due to schema changes and unexpected failure.
    ![elt_example](./docs/elt_example.png)
    - External table makes ELT process easier to be implemented reducing the gap between data lake and data warehouse, but still can be benefited from partitioning by ***Hive-style Partitioning*** 
    - Actually, Parquet files embed data schema into the files. We can use some operators that support referring parquet internal schema to create external tables in data warehouse. So, we don't have to pre-define schema for every tables, except within an stardardized data processing framework.
    - Transformer from *Bronze* layer to *Silver* layer can be a custom framework that stardardizes data format and follows company's data governance. There's multiple relevant libraries can be mentioned here, such as ***pyspark***, ***dlt***, and etc. depended on data sources, acceptable cost, and team expertise in tools.
    - There're also multiple tools that support transforming data from *Silver* layer to *Gold* layer such as ***dbt***, ***SQL Mesh***, and etc. or even native airflow operator. Such tools give ability to visualize transformation logic and enable data lineage, native integrated data dict for a better maintainance.
        - Many companies discourage the use of these tools giving the reason that it's not appropriate for big scale projects and too messy to maintain. However, I disagree this because there're practices and principles that solve this problem, like ***Data Mesh*** *(twisted from Domain-driven design: DDD)* and ***Modularity***. 
        - Anyway, it requires highly skilled data archietct and data engineer to develop and maintain these tools along with the priciples. So, they might not be able to focus this enough since it can be quite a low-level foundation and very far from a product that's seemed to be more profitable to the company.

## 3. Web Scraping

This part is not currently in development. I will update the progress later. But, you can check the concept and the old written code in [web-scraping](https://github.com/Patcharanat/ecommerce-invoice/tree/master/web-scraping) folder.

## 4. EDA and Data Visualization

Once we have the data in the data warehouse, we can do the EDA and data visualization connecting data from the data warehouse. I will use **PowerBI** to create the dashboard, and Python for some ad-hoc analysis.

### 4.1 EDA

Actually, we might have to do the **EDA** (Exploratory Data Analysis) before loading data to data warehouse to see how we would clean the dataset, but in the analysis part, we can do in different objectives. In this part, I will do an EDA to see the characteristic of the data, and see if there is any insight that can be meaningful to the business.

<details><summary>Data Characteristics</summary>
<p>

This part is mostly done with Python by **Pandas** and **Matplotlib**, because of its flexible.

- `CustomerID` contains null values
    - fill null values with int 0 → for RFM, CustomerID 0 will be removed
- `Description` contains null values
    - fill null values with “No Description”
- `Description` contains different descriptions for the same stock code
    - replace the most frequent description → for market basket analysis
- `UnitPrice` contains negative values
    - StockCode "B": adjust bad dept
- `Quantity` contains negative values means the refund
- `Quantity` and `UnitPrice` contain outliers
    - need to be removed for model development
    - should be kept for revenue analysis
- `Quantity` < 0 & `UnitPrice` = 0 → Anomaly 
    - should be removed for model development
    - should be kept for revenue analysis
    - should be filtered out for market basket analysis
    - it can be something, like damagae, manually filled, etc.
- `InvoiceNo` contains "C" → refund
- Inconsistent `StockCode`
    - "D" → discount
    - "M" → manual (there's also "m")
    - "S" → sample
    - "BANK CHARGES" → bank charges
    - "POST" → postage
    - "DOT" → dotcom postage
    - "CRUK" → charity
    - "PADS" → pads to match all cushions
    - "C2" → carriage
    - the digits StockCode with a letter → the same product but different colors
- More from random data description: `UnitPrice` is in "Pound sterling" 
- `Country` mostly contains "United Kingdom" → more than 90% of the data
- `InvoiceDate` includes time, but not in the same timezone, for different countries

</p>
</details>

<img src="./src/Picture/boxplot_outlier.png" width="75%">

You can check the code in [**ecomm_eda.ipynb**](ecomm_eda.ipynb) file.

### 4.2 PowerBI Dashboard

Since, the current version of PowerBI has a bug of connecting to data warehouse, I will connect the data from local parquet file that loaded from data warehouse instead.

We can connect parquet file locally to Power BI:
- Go to `Get Data` > Type in `"Parquet"` > `Connect` > use Basic option, and type in URL box by this: `file:///C:/path/to/data.parquet` > Then, click OK

*Note: you have to change the path to your local path*

Now we can see the data in PowerBI, and do the data visualization.

![ecomm_pbi](./src/Picture/ecomm_pbi.jpg)

I won't go into detail of how to create the dashboard or each component, but you can download and check it yourself in [**ecomm_bi.pbix**](ecomm_bi.pbix) file.

What worth to mention are:
- I used **DAX** to calculate Growth Rate as a measure that would be quite complex for some people who are not familiar with PowerBI or DAX, but it used just regular formula as: `(Sales in the Current Context month - Sales in the Previous month) / Sales in the Previous month`. I also used `CALCULATE` function to calculate the previous month value together with `ALLSELECTED`, and `DIVIDE` function to calculate the growth rate.
- I linked variables between reports to be able to **Drill Through** to other reports, making the dashboard more interactive, and more in-depth to analyze.

A little note for future myself:
- **Dashboard is about Storytelling**, so it's better to have a story in mind before creating the dashboard. It's not just about the data, but how to arrange the story from the data.
- **It's crucial to know who are the audiences of the dashboard, and what the objective of the dashboard is**. So, we can select the right metrics, right data, and right visualization.
- **Data model is very important**, it's the foundation of the dashboard. If the data model is incorrected, the dashboard will be wrong also. If the data model come in a good shape, the dashboard will be easier to create, and the data will be easier to analyze. (especially in aspect of **Time Intelligence**)

### 4.3 Data Modeling and Optimization in Production
This topic is quite important and partially related with data engineering processes, since it can be highly involved in cost optimization.
- Although *ingestion* process is completed, we might need to transformed it, besides of raw cleaned and normalized data, with custom business logic, and tables aggregation to further analyze and exploit more from data.
- This process usually referred to *ELT* or *transformation* that is not the same *transformation* in ingestion process, which is just controling data quality by casting type, formatting date/timestamp or mapping data into specified schema by a framework.
- Transformed data models can be located in *curate* or *gold* layer in *medallion architecture*, but sometimes can be in *semantic layer* which is referred to another transformation sub-layer before being shown on dashboard. However, this depends on companies' data archietcture and agreement between teams.
![semantic-concept](./src/Picture/semantic-concept.jpg)
- Transformation process can be done with SQL by analytic engineer, data analyst, domain expert, and etc. to make data become more meaningful to business aspect. However without proper expertise in SQL and data modeling, cost from dashboard usage and data preparation can be gone in a very wrong way.
- Tools that support transformation at aggregation level is emerging, since ELT pattern is still counted as modern at the moment for batch data engineering pipeline. Some of famous tools you might have heard could be *dbt*, and *SQLMesh* which enable ability to perform complex incremental data loading logic, SCD handling, data lineage, data dict, and built-in data quality controlling at high level. However, you could still implement data aggregation with native airflow operator introduced by official provider by executing sql directly to data warehouse through Airflow.

#### How to Optimize Data Models
- What should be considered in gold layer (or curated) is technical aspects such as, SCD (Slow Changing Dimension), snapshot and incremental transformation (which usually involved with how ingestion pipelines work and silver layer partitioning), data transferring behavior or ingestion method (full dump, append, delta, or replace), and business logic (if semantic layer not exists or it required pre-calculation in gold layer)
- **Pre-calculated table was proved to be more optimized when data is queried to dashboard. Moreover, data aggregation with only necessary partitioning considered also important in cost optimization when it come to larger scale in production database.**
- Using view not only prevent downstream users from modifying table in ideal, but also manipulate the users to query from only specific period of data or partition resulting in lesser data scanning per read or per dashboard refresh.
    - Using view can futher lead to *data governance* issues such as user permission to read from both table and view if not considering dashboard permission. 
- Modeling data warehouse to *star schema* or *snowflake schema* (considered to be fact/dimension pattern) is claimed multiple times to be more cost optimized, but it lack of quantitative evidence.


## 5. Machine Learning Model Development

The Model Development part is not fully finished yet, but some part of it are done and ready to be presented.

This is what I have planned so far:
1. [Customer Segmentation By RFM, KMeans, and Tree-based Model](#51-customer-segmentation-by-rfm-kmeans-and-tree-based-model) ***(Done)***
2. [Market Basket Analysis](#52-market-basket-analysis) ***(Done)***
3. [Demand Forecasting](#53-demand-forecasting) ***(Paused)***
4. Recommendation System *(Not started)*
5. Customer Churn Prediction *(Not started)*
6. Price Analysis and Optimization *(Not started)*

You can see the code in [**model_dev.ipynb**](model_dev.ipynb)

### 5.1 Customer Segmentation By RFM, KMeans, and Tree-based Model

**Introduction**

**RFM (Recency, Frequency, Monetary)** is a well known method to segment customers based on their behavior. **But recency, fequency, and monetary alone, are not effective enough to segment the diversity of customers**. We should use other available features or characteristics of customers to segment them more effectively that come to the harder to score with traditional RFM method.

As a result, **KMeans emerged as a crucial machine learning technique for reasonably effectively clustering clients** into more precise customer segments. **But, the Kmeans is not interpretable**, we can't explain the result or criteria to the business of how clusters are formed or how the customers are segmented, but only show what features we use in KMeans model (we don't even know which features are more influence).

**So, we can use Decision Tree to find the criteria of the clusters**, and explain the result to the business, leading to proper campaigns and strategies that suit to customer segments to be launched.

Moreover, we can use **XGBoost to find the most important features that influence the customer segments (or each segment)**, and further concern and develop strategies regarding that features.

#### **RFM and Features Details**

First, we will form the RFM table based on customer transactions and add some more features (Feature Engineering) that we think it might be useful for segmentation which include:
- Recency
- Frequency
- Monetary
- is one time purchase
- mean time between purchase
- mean ticket size (average total price of each purchase)
- mean of number of unique items of each purchase
- mean quantity items of each purchase
- mean spending per month
- frequency of purchase per month
- (refund rate)

Eventually, we will get a new table that represents customers profile and their behavior, this table is a `rfm` variable in the code in [model.dev](model_dev.ipynb).

*Note: The features we used to decribe the customer behavior is not limited to the features above, we can add more features that we think it might be useful for segmentation, but also should be interpretable for initiaing the campaigns and strategies, so some features, like standard deviation, might not be appropriate for this case.*

#### **KMeans**

Before we put the customer profile data into KMeans, we should scale the data first , in my case I used **Robust Scaler**, to make the data have the same scale, since KMeans algorithm use euclidean distance to calculate the clusters, so it could sensitive to the different scale of the data.

Then, we will use KMeans to segment customers into clusters. We will use **Elbow Method** and **Silhouette Plot** to find the optimal number of clusters which eventually is 10 clusters.

<img src="./src/Picture/kmeans-elbow.png" alt="kmeans-elbow" width="75%">

![kmeans-silhouette](./src/Picture/kmeans-silhouette.png)

Then, we label the clusters to customer profile table which not scaled yet, so we can see the customer profile of each cluster with the original scale to make it more interpretable. We will use this table to find the criteria of the clusters as an input and validation set for the Decision Tree.

References:
- [Selecting the number of clusters with silhouette analysis on KMeans clustering](https://scikit-learn.org/stable/auto_examples/cluster/plot_kmeans_silhouette_analysis.html)
- [Segmenting Customers using K-Means, RFM and Transaction Records](https://towardsdatascience.com/segmenting-customers-using-k-means-and-transaction-records-76f4055d856a)

#### **Decision Tree**

After that, we will use **Decision Tree** to find the criteria of the clusters to make the clustering result from KMeans become interpretable. I used **Random Search** with **Cross Validation** to find the best hyperparameters of the Decision Tree to make it the most accurate **resulting in accuracy 91.41% on test set, 94.11% on train set, macro averaged of F1 score 0.75, to clarify criteria of each cluster.**

![kmeans-tree](./src/Picture/kmeans-tree.png)

***Note: The 91% accuracy doesn't mean we segmented the customers correctly by 91%**, because we can't be sure that Kmeans correctly 100% segmented the customers (and definitely, it didn't), but we can tell that the Decision Tree can explain the criteria of the clusters correctly by 91% in generalization, So we can take account of the criteria from the Decision Tree to cluster customer segmented to follow Kmeans result.*

#### **XGBoost**

Finally, we will use **XGBoost** to find the most important features that influence the customer segments or important factors to develop the strategies. I also used **Random Search** with **Cross Validation** to find the best hyperparameters of XGBoost resulting in accuracy 97.76% on test set, 100% on train set, macro averaged of F1 score 0.77, to find the most important features (seems overfitting, but it's not a main focused).

You may heard of feature importance from XGBoost that can describe which features are more influence to the model, but it's not effective enough due to its limitation, like how it treats the correlated features, how differently treats the categorical features and numerical features, and how it's not generalized to other models. So, I used **Permutation Feature Importance** instead, which is more interpretable and generalized for choosing the most influence features to each cluster. Moreover, it can be used with any model, not just XGBoost.

References:
- [Permutation feature importance - sklearn](https://scikit-learn.org/stable/modules/permutation_importance.html#permutation-importance)
- [Permutation Importance vs Random Forest Feature Importance (MDI)](https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance.html#sphx-glr-auto-examples-inspection-plot-permutation-importance-py)

The most important features for each cluster can be shown in the plot below:

<img src="./src/Picture/permutation_feature_importance.png" alt="permutation_feature_importance" width="75%">

Finally we can classify the customers into 10 clusters and explain the criteria of each cluster to the business.
- **Cluster 0** : Bought less, not often, and small ticket size, I think this is a cluster of casual customers or one-time purchase customers.
- **Cluster 1** : Bought much in amount, but low quantity.
- **Cluster 3** : Bought less in amount, but bought often, and small ticket size, I think this is a cluster of regular customers who are likely to active and easily attracted by marketing campaign.
- **Cluster 4** : Big spenders, and bought a lot of items both quantity, and diverse items, I guess this is a cluster of wholesale customers.
- **Cluster 5** : Also Big spenders, and bought a lot of items both quantity, and diverse items, I also think this is a cluster of wholesaler but bigger than cluster 4, because they bought in more amount and more quantity.
- **Cluster 7** : Big spenders, but not much as cluster 5, spent 50 - 155£ per month and bought once a month approximately, and also bought in low quantity. I guess this is a cluster of valuable regular customers that we should keep. Moreover, they're also the largest group among all clusters.

... and so on.

*Note: the more cluster and the more depth you have, the more complex and specific the criteria of each cluster will be, leading to harder to classify.*

### 5.2 Market Basket Analysis

The Market Basket Analysis is a technique to find the association between items that customers purchase together. It can be used to find the relationship between items, and use the result to develop strategies such as cross-selling, and product bundling.

**The important metrics** of Market Basket Analysis are:
- **Support**
    - how frequent the itemset appears in the dataset
    - can be calculated by: *support(itemset) = count_basket(itemset) / total_count_basket*
    - support score range from 0 to 1, "minimum support" can be used to filter out itemset that are not frequent (threshold depends on user and dataset)
- **Confidence**
    - how likely item B is purchased when item A is purchased
    - confidence(A→B) = count_basket(itemset (A and B)) / count_basket(A)
    - confidence score range from 0 to 1, "minimum confidence threshold" can be used to filter out itemset that are not meet the requirement (threshold depends on user and dataset)
- **Lift**
    - how likely item B is purchased when item A is purchased, how many times probability increase or decrease compared with normal B purchased
    - lift(A→B) = confidence(A→B) / support(B)
    - lift score range from 0 to infinity *(in times unit)*
    - lift > 1 → B is likely to be purchased when A is purchased
    - lift < 1 → B is unlikely to be purchased when A is purchased
    - lift = 1 → B is independent from A

The Market Basket Analysis can be done by using **Apriori Algorithm** which is a popular and effective algorithm to find the association between items. one can use **mlxtend** library to implement Apriori Algorithm following these steps:
- **Step 1**: Find frequent itemset (itemset that meet the minimum support threshold)
- **Step 2**: Generate association rules from frequent itemset (itemset that meet the minimum confidence threshold)
- **Step 3**: Sort the rules by lift
- **Step 4**: Visualize the rules as a table and interpret the result

What challenges in market basket analysis are data preparation, specifying threshold of each metric, and interpret the result to the business. It's can be done easily and useful for the retail business.

for example of the result of market basket analysis can be shown in the table below:

Antecedents | Consequents | Support | Confidence | Lift
:---: | :---: | :---: | :---: | :---:
PINK REGENCY TEACUP AND SAUCER | GREEN REGENCY TEACUP AND SAUCER | 0.034121 | 0.828530 | 15.045681
GREEN REGENCY TEACUP AND SAUCER | PINK REGENCY TEACUP AND SAUCER | 0.034121 | 0.619612 | 15.045681
PINK REGENCY TEACUP AND SAUCER | ROSES REGENCY TEACUP AND SAUCER | 0.031806 | 0.772334 | 13.714834
... | ... | ... | ... | ...
LUNCH BAG BLACK SKULL. | LUNCH BAG PINK POLKADOT | 0.030560 | 0.425620 | 6.896678

*Note: The table is snippet from the result of market basket analysis*

We can interpret the result as:
- *PINK REGENCY TEACUP AND SAUCER* and *GREEN REGENCY TEACUP AND SAUCER* are **frequently purchased together**, the itemset appeared by 3.41% of total transactions **(considered by support score)**

    *Note: In our case, we filter out single item purchase transaction, hence the 3.14% is the percentage of transactions that contain both 2 or more items which is `basket_encoded_filter` variable in the [notebook](model_dev.ipynb) resulting in 15660 x 0.034121 = 534 transactions out of 16811 transactions.*

- **the probability** of *GREEN REGENCY TEACUP AND SAUCER* **purchased when** *PINK REGENCY TEACUP AND SAUCER* **purchased** is 82.85% **(high confidence)**
- **the probability** of *GREEN REGENCY TEACUP AND SAUCER* **purchased** when *PINK REGENCY TEACUP AND SAUCER* **purchased** is 15.04 **times higher than alone** *GREEN REGENCY TEACUP AND SAUCER* **purchases (high lift)**
- the second row (or rule) is the same as the first row, but the consequent and antecedent are swapped, so we can watch the result from both sides
- the third rule and so on, show the bundle of item that are frequently purchased together, these rules can be used to develop strategies such as cross-selling, product bundling.

References:
- [How To Perform Market Basket Analysis in Python - Jihargifari - Medium](https://medium.com/@jihargifari/how-to-perform-market-basket-analysis-in-python-bd00b745b106)
- [Association Rule Mining using Market Basket Analysis - Sarit Maitra - Towards Data Science](https://towardsdatascience.com/market-basket-analysis-knowledge-discovery-in-database-simplistic-approach-dc41659e1558)

### 5.3 Demand Forecasting

In this section, we will use **Time Series Forecasting** technique to predict future values based on the past values of the data. we will use some input from the past as features to predict the future sales.

In general, we use current features or features that already happened fed into the model to predict the sales as a target. But, the problem is, if we want to predict the sales of the next month, we don't have the input of the next month yet. So, we have to use the records of the past to predict the sales of the next month.

Therefore, we have to perform feature engineering, transform data, create features to obtain the appropriate and effective features to predict the future sales. So, we will use **Lag Features** and **Rolling Window Statistics**.

But how can we know how much lag of the features and how many rolling window statistics should we use? first we can use **Auto-correlation** to find the optimal lag value or candidates to be used as lag features. Then, we can use **Cross-Validation** to find the optimal number of rolling window and the best candidate of lag features.

<img src="./src/Picture/autocorrelation.png">

Additionally, I used **Fast Fourier Transform** to find seasonality of the data, which is the pattern that repeats itself at regular intervals of time. The seasonality can be used to create features to predict the future sales.

<img src="./src/Picture/fourier.png" width="75%">

Personally, I thought using fast fourier transform to find seasonality is quite more quantitative than using autocorrelation. But, we can use both of them to find the seasonality of the data to ensure the result.

![predict-demand](./src/Picture/predict-demand.png)

I think the most challenging part of timeseries forecasting is to find the appropriate features to predict the future sales. The features that we use to predict the future sales should be the features that already happened in the past, and we can't use the features that will happen in the future. So, checking how much lagged values of the features can be significant to predict the future sales.

Model | RMSE | MAPE
:---: | :---: | :---:
Baseline (Mean) | 3170.143 | 27.16%
LightGBM | 4884.230 | 32.29%

*(Current Result)*

Even we can see that the prediction result can a bit capture the trend of the data, but the result is not good enough compared with **mean** of the target.

I intended to **decompose** the data into trend, seasonality, and residual, then use them as features to predict the future sales to make it stationary **and also add moving average types** such as EMA (Exponential Moving Average) and LWMA (Linear Weighted Moving Average) to the model, to weight the recent data more than the old data. Moreover, I want to test traditional statistical model such as ARIMA, and SARIMA. But, I think it's enough for now, I will update the model later.

References:
- [How to Calculate Autocorrelation in Python?](https://www.geeksforgeeks.org/how-to-calculate-autocorrelation-in-python/)
- [How to detect seasonality, forecast and fill gaps in time series using Fast Fourier Transform](https://fischerbach.medium.com/introduction-to-fourier-analysis-of-time-series-42151703524a)
- [How To Apply Machine Learning To Demand Forecasting (Concept)](https://mobidev.biz/blog/machine-learning-methods-demand-forecasting-retail)
- [All Moving Averages (SMA, EMA, SMMA, and LWMA)](https://srading.com/all-moving-averages-sma-ema-smma-and-lwma/)
- [Finding Seasonal Trends in Time-Series Data with Python](https://towardsdatascience.com/finding-seasonal-trends-in-time-series-data-with-python-ce10c37aa861)
- [Various Techniques to Detect and Isolate Time Series Components Using Python (Technical)](https://www.analyticsvidhya.com/blog/2023/02/various-techniques-to-detect-and-isolate-time-series-components-using-python/)

### 5.4 Recommendation System

*Not started . . .*

### 5.5 Customer Churn Prediction

*Not started . . .*

### 5.6 Price Analysis and Optimization

*Not started . . .*

## 6. ML Code Productionization and Deployment

After we developed and evaluated the model, we can deploy the model to production to leverage the business, bringing the model out from the Python notebook or your lab, and not only making it available to the data scientist.

We can deploy the model to production in many approaches, please refer to this repo: [MLOps - ML System](https://github.com/patcha-ranat/MLOps-ml-system) for further details of principles and research on *MLOps* methodology. However, most approaches required *docker container* for consistent runtime even in different environments, so I will elaborate more on containerization for this topic.

![deploy-overview](./src/Picture/deploy-overview.png)

***Due to latest revise (Nov 2024), I decided to re-write this from [the previous version of this chapter](https://github.com/patcha-ranat/Ecommerce-Invoice-End-to-end/blob/7f57532552d5c948054753bbc0877d370cafd200/README.md#6-model-deployment-and-monitoring) into a new one, emphasizing less on typical concepts and focusing more on specific use case for this project. However, considering how huge scale of this project was, I also intended to separate this chapter into [MLOps - ML System](https://github.com/patcha-ranat/MLOps-ml-system?tab=readme-ov-file#mlops---ml-system) project to clarify more on my most interested topic in detail.***

*Anyway, documentation for this topic will mostly focus more on overview concepts of packaging ML code to be ML pipeline with airflow dag integration and together with deployment on cloud through CI/CD Workflow. Interface service of inferencing such as an API with backend database and Model Monitoring, will be further implemented on, again [MLOps - ML System](https://github.com/patcha-ranat/MLOps-ml-system).*

Although this project introduced multiple ML use cases, I choose [Customer Segmentation By RFM, KMeans, and Tree-based Model](#51-customer-segmentation-by-rfm-kmeans-and-tree-based-model) to be deployed with *precompute serving pattern*, so there's no model wrapped into a container or prediction API service, just ML Pipeline within docker container deployed with CI/CD Pipeline.

*MLOps Code Structure and Logic*
![kde-ecomm-mlops-code-structure](./src/Picture/kde-ecomm-mlops-code-structure.png)

*MLOps Code Workflow*
![kde-ecomm-mlops-code-workflow](./src/Picture/kde-ecomm-mlops-code-workflow.png)

### 6.1 Exporting from Notebook

First, we will focus on extracting the model development processes from notebook and transforming it into python module with *factory* pattern using `argparse` library and *OOP* concept. Some processes were improved to be more appropriate to be operated automatically through pipeline. Such as:
- How data read/written into ML code
    - Reader and Writer classes are implemented to support feeding input and retrieving output from ml service both local and cloud environments.
- Selecting K Value
    - Since now we can't consider optimal k value qualitatively by human through automated pipeline, clarifying logic/rules to find optimal K now become important.
    - Here is the logic represented in math:
    ![dynamic_k_equation](./src/Picture/dynamic_k_equation.png)
- Model Development Changes
    - Changing feature engineering process imputing recency feature from `999` to the real recency
    - Replacing interpretation method from decision tree or xgboost feature importance with LightGBM and permutation feature importance for more interpretable and quantitative measurement.
    - *(please, check [ML-Sandbox/dynamic_segmentation/revise_ecomm_logic.ipynb](https://github.com/patcha-ranat/ML-Sandbox/blob/main/dynamic_segmentation/revise_ecomm_logic.ipynb) for final ML Logic)*
- Model Retaining Triggering is now implemented
- Final output will be 2 data models, 2 ML models and artifacts (metadata + control file) and scaler.
    - please check folder `code/models/output/` for output example
    - [df_cluster_importance.parquet](./code/models/output/data/2024-11-08/df_cluster_importance.parquet)
    - [df_cluster_importance.parquet](./code/models/output/data/2024-11-08/df_cluster_importance.parquet)

#### Related Files
- [code/models/main.py](./code/models/main.py) : entrypoint of the application using argparse
- [code/models/abstract.py](./code/models/abstract.py) : abstract classes defining overview of implemented classes
- [code/models/io_services.py](./code/models/io_services.py) : Input and Output related services (reader/wrtier)
    - `InputLocalReader`: Reader for input *(data and interpreter if exists)* on local
    - `InputGCPReader`: Reader for input *(data and interpreter if exists)* GCP cloud
    - `InputProcessor`: Reader type selector (factory) based on argparse argument
    - `OutputLocalWriter`: Writer for output on local
    - `OutputGCPWriter`: Writer for output on GCP Cloud
    - `OutputProcessor`: Writer type selector (factory) based on argparse argument
- [code/models/ml_services.py](./code/models/ml_services.py) : ML Code Logic as a pipeline including,
    - `CustomerProfilingService`: RFM - pre-processing, feature engineering to formulate RFM DataFrame
    - `CustomerSegmentationService`: Clustering service, related to using KMeans model, and cross-validation automated finding optimal K value.
    - `ClusterInterpretationService`: Interpretation service related to training/retraining LightGBM and utilizing permutation feature importance to find influenced features for each cluster
    - `MLProcessor`: Orchestrator of overall ML services
- [code/models/requirements.txt](./code/models/requirements.txt) : Python dependencies used in the app
- [code/models/Dockerfile](./code/models/Dockerfile) : Packaging the app and dependencies to a docker container, installing additional components as app required (e.g. lightgbm prerequisites)

**Please refer to [code/models/README.md](./code/models/README.md) for example of command usage.**

### 6.2 Docker Containerization

After python module works properly on local machine, we will package the code into docker container for the next step by [code/models/Dockerfile](./code/models/Dockerfile) file.

*Note: What worth to mention is that the path specifying in the Dockerfile is relative to the current working directory where we execute the `docker build` command. So, we have to be aware of the path we specify in the Dockerfile and how we execute the file via Command Line Interface (CLI).*

With [a few research](https://stackoverflow.com/questions/24537340/docker-adding-a-file-from-a-parent-directory), I found that it's not possible to specify the path to copy the files from the parent directory.

And when we execute the command, we have to be in the ***./code/models/*** realative to root of the project and use this command pattern:

```bash
# workdir: ./code/models/

docker build -t <image-name>:<tag> -f <path-to-dockerfile> <path-to-working-directory>
# -t: tag the image with the name
# -f: (Optional) specify the path to Dockerfile that we want to execute. Required when multiple Dockerfiles exist in the same working directory

# which can lead to this command
docker build -t ecomm/interpretable-dynamic-rfm-service:v2 .
```

1. Before packaging code into docker container, we have to make sure it works as expected within local environment.
    ```bash
    # test module local
    python main.py --env local --method filesystem --input_path '../../data/ecomm_invoice_transaction.parquet' --output_path output --exec_date 2024-11-03

    # test module local force_train
    python main.py --env local --method filesystem --input_path '../../data/ecomm_invoice_transaction.parquet' --output_path output --exec_date 2024-10-29 --force_train

    # test module against gcp
    # TODO: Replace with your bucket name
    python main.py --env gcp --project_id <project_id> --method filesystem --input_path 'gs://<landing_bucket_name>/input/data/2024-11-03/ecomm_invoice_transaction.parquet' --output_path 'gs://<staging_bucket_name>/output' --exec_date 2024-11-03
    ```
    *Note: Please refer to [initial_gcp.sh](./code/models/test/initial_gcp.sh) before testing against cloud environment*
2. After packaging code into docker container, we have to make sure that its functionality both local and cloud method work perfectly within the container
    ```bash
    # test module local via docker
    docker run \
        ecomm/interpretable-dynamic-rfm-service:v1 \
        --env local \
        --method filesystem \
        --input_path 'ecomm_invoice_transaction.parquet' \
        --output_path output \
        --exec_date 2024-10-29

    # test module against gcp via docker
    # TODO: Replace with your bucket name
    docker run \
        -v $HOME/.config/gcloud:/root/.config/gcloud \ # mount GCP default credential
        ecomm/interpretable-dynamic-rfm-service:v2 \
        --env gcp \
        --method filesystem \
        --input_path 'gs://<landing_bucket_name>/input/data/2024-11-03/ecomm_invoice_transaction.parquet' \
        --output_path 'gs://<staging_bucket_name>/output' \
        --exec_date 2024-11-03
    ```

If all steps work perfectly, we can now go to the next step: deploy to cloud

### 6.3 Deploying the Model to the Cloud Environment

After we have everything ready, we will deploy containerized ML Pipeline to cloud environment utilizing Google Artifact Registry (GAR), similar to *Docker Hub* but more secured within GCP.

So, what we need to do is:
1. **Prepare cloud environment and authentication**
2. **Build the Docker image locally and push it to the Artifact Registry**

#### 1. Prepare cloud environment and authentication

First, you need to install '*Google Cloud CLI (gcloud/Cloud SDK)*' to make you more convenient to interact with gcp resources beyond web-based UI. Check installation completion by running `gcloud --version`.

Rerference:
- [Install the gcloud CLI - Google Cloud Platform](https://cloud.google.com/sdk/docs/install)

For the sake of this topic and the next, please add this following roles for sufficient permissions:
- **Artifact Registry Admin**: *For creating/deleting Artifact Registry object*
- **IAM Workload Identity Pool Admin**: *For creating/deleting Workload Identity Federation (WIF) Pool*
- **Service Account Token Creator**: *For account impersonation*
- **Workload Identity User**: *For granting access from WIF to the service account*

![deploy-access-example](./src/Picture/deploy-access-example.png)

In the previous Terraform section, the steps are introduced to use '*static credentials*', loaded from cloud to local machine, to authenticate with GCP. But in this revised version, I will use *Application Default Credentials (ADC)* impersonated with a service account to authenticate between Terraform and GCP.
- *ADC* is a method to authenticate to GCP interactively through CLI via *gcloud*. It's a proper authentication method when there's human involved between the processes, but impossible with automated pipeline.
- ADC method let us login to GCP with email address through web browser interactively, and then it store a credential to gcloud default path to look for automatically when we try to authenticate with GCP with gcloud

Please, run these commands to authenticate with impersonated account
```bash
# For first time using gcloud
gcloud auth login

# Logic through impersonated account through ADC method
gcloud auth application-default login --impersonate-service-account <SERVICE_ACCT_EMAIL>

# Set project
gcloud config set project <project_id>
```

Then we execute these terraform configs
- [/code/models/terraform/main.tf](./code/models/terraform/main.tf) together with [/code/models/terraform/variables.tf](./code/models/terraform/variables.tf)
- [/code/models/terraform/auth/main.tf](./code/models/terraform/auth/main.tf) together with [/code/models/terraform/auth/variables.tf](./code/models/terraform/auth/variables.tf)
by
```bash
# workdir: code/models/terraform
terraform init
terraform plan
terraform apply
terraform destroy

# workdir: code/models/terraform/auth
terraform init
terraform plan
terraform apply
# terraform destroy
```
*Note: WIF shouldn't be created/deleted repeatedly, refer to [Stack Overflow - Terraform on GCP - Error 409: Requested entity already exists](https://stackoverflow.com/a/73944443)*
```bash
Error: Error creating WorkloadIdentityPool: googleapi: Error 409: Requested entity already exists
```

If below error occurred, please check if you have the '*Service Account Token Creator*' role in both owner account and service account. if yes, please try to reset `$GOOGLE_APPLICATION_DEFAULT` environment variable by `unset $GOOGLE_APPLICATION_DEFAULT`, restarting terminal and try to authenticate with `gcloud` with the above process again.
```bash
{
  "error": {
    "code": 403,
    "message": "Permission 'iam.serviceAccounts.getAccessToken' denied on resource (or it may not exist).",
    "status": "PERMISSION_DENIED",
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
        "reason": "IAM_PERMISSION_DENIED",
        "domain": "iam.googleapis.com",
        "metadata": {
          "permission": "iam.serviceAccounts.getAccessToken"
        }
      }
    ]
  }
}
```

References:
- Terraform Code
    - [terraform-google-github-actions-runners - main.tf - Github](https://github.com/terraform-google-modules/terraform-google-github-actions-runners/blob/master/modules/gh-oidc/main.tf)
    - [terraform-google-github-actions-runners - variables.tf - Github](https://github.com/terraform-google-modules/terraform-google-github-actions-runners/blob/master/modules/gh-oidc/variables.tf)
    - [Example Usage - Iam Workload Identity Pool Provider Github Actions - Terraform](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/iam_workload_identity_pool_provider#example-usage---iam-workload-identity-pool-provider-github-actions)
- Debugging Authentication
    - [Terraform on GCP - Impersonation not working (missing permission in generating access token)](https://stackoverflow.com/a/76110825)
    - [Authentication for Terraform - Google Cloud Platform](https://cloud.google.com/docs/terraform/authentication)

#### 2. Build the Docker image locally and push it to the Artifact Registry
To puslish created docker image to GAR, please run the following commands:
```bash
# workdir: code/models/
# gcloud auth application-default login --impersonate-service-account <SERVICE_ACCT_EMAIL>

# gcloud configure docker
gcloud auth configure-docker "<$REGION>-docker.pkg.dev"

# Build image locally
docker build -t <any-image-name> .

# Change image name locally to acceptable format for GAR 
docker tag <previous-step-image-name> <$REGION>-docker.pkg.dev/<$PROJECT_ID>/<$REPOSITORY>/<$IMAGE_NAME>:<$TAG>

# Push image to GAR
docker push <$REGION>-docker.pkg.dev/<$PROJECT_ID>/<$REPOSITORY>/<$IMAGE_NAME>:<$TAG>
```
Check the result, pushed image, at artifact registry gcp service.

*Note: You can export the environment variables to avoid typing the same variables over and over again, reducing the chance of making a mistake.*

Reference:
- [Push and pull images - Google Cloud Platform](https://cloud.google.com/artifact-registry/docs/docker/pushing-and-pulling)

### 6.4 CI/CD Workflow - Automated Deployment Process

When we make changes on the app service, we certainly need to re-deploy it to the cloud environment with a newer version for improvement on production. But, we don't want to do it manually every time, especially on production environment, which can cause error-prone and time-consuming process. So, this come to the important of automating the deployment process or CI/CD Workflow. CI/CD Pipeline make sure your developed application is well-maintained, qualified with tests, and deploy securely in predictable way without error-prone issue.

![cicd-workflow-trigger-example](./src/Picture/cicd-workflow-trigger-example.png)

*Github Actions (GHA)* is one of many CI/CD tools that we can use to automate the deployment process. It can automate tasks when we manually trigger it or with specific events we specified as its condition within the workflow. For example, we can automate the deployment process when we push on specific branch or create pull request with a certain branch to the repository.

![cicd-workflow-example](./src/Picture/cicd-workflow-example.png)

GHA workflow and code logic is not different from manual deployment process, including installing gcloud, authentication, building docker image from source code in GitHub, and pushing to specified image registry, except we can do this all processes with a few click. However, GHA workflow has its own syntax and some specific feature such as using pre-defined action, and accessing variables and GitHub default variables which make it a bit more complicated than regular bash command such as:

```yaml
# Using Environment Variable
echo $ENV_VAR

# This equal to above, but more useful in f-string scenario
echo ${ENV_VARIABLE}

# This call GitHub default variables
echo ${{ github.ref_name }}

echo ${{ inputs.xxx }}

echo ${{ env.xxx }}

# secret variable will be masked with '****' in GHA logs 
echo ${{ secrets.xxx }}

echo ${{ steps.STEPS_ID.outputs.* }}

# Example of Other GHA Syntax
...
runs-on: ubuntu-latest
    steps:
        - name: step name 1
          id: step_id_1
          uses: repo/action@v1
          with:
            xxx: xxx
        
        - name: step name 2
          id: step_id_2
          run: |
            echo xxx
...
```

Related Files:
- [.github/workflows/build-deploy-model.yml](./.github/workflows/build-deploy-model.yml) : CD Workflow
- [.github/workflows/pull-request-ci.yml](./.github/workflows/pull-request-ci.yml) : CI Workflow

#### Github Actions - Secrets Variable and Authentication

The most important aspect for *Continuous Deployment (CD)* Workflow is authentication, because we need to make some changes to cloud resources. Traditionally, using long-lived credentials just like password through ***GHA secrets variables*** is the most typical and straightforward solution.
- You have to get a credential file and copy its contents
- Go to **Repo** > **Settings** > **Secrets and variables** > **Actions**
- Create **New repository secret**, suppose secret name: `GCP_PASSWORD` and paste credential content as *Secret*
- Now, you can use the secret for authentication
    ```yaml
    - uses: 'google-github-actions/auth@v2'
      with:
        credentials_json: '${{ secrets.GCP_PASSWORD }}'
    ```

However, this long-lived credential is considered as security risk. So, there's a new service from GCP called *'Workload Identity Federation' (WIF)* which introduce authentication without credentials i.e. keyless authentication.

WIF is quite complex in architecture perspective, but for usage, we just need service account email (without credential), WIF Pools, WIF Provider, and some additional step for granting service account access.

- WIF in GHA
    ```yaml
    steps:
        - name:  Authenticate GCP - Workload Identity Federation
          uses: 'google-github-actions/auth@v2'
          with:
            project_id: ${{ secrets.PROJECT_ID }}
            workload_identity_provider: ${{ secrets.WIF_PROVIDER_URL }}
            service_account: ${{ secrets.SERVICE_ACCOUNT }}
    ```
    - we can see that it require no credential, but exposing security components or architecture may lead to security risk also.
- WIF in Terraform
    - [code/models/terraform/auth/main.tf](./code/models/terraform/auth/main.tf)
    - Keys to enable this services are: `attribute_mapping`, `attribute_condition`, and `issuer_url`
    ```
    resource "google_iam_workload_identity_pool_provider" "main_provider" {
        project                            = var.project_id
        workload_identity_pool_id          = google_iam_workload_identity_pool.main_pool.workload_identity_pool_id
        workload_identity_pool_provider_id = var.provider_id
        display_name                       = var.provider_display_name
        description                        = var.provider_description
        attribute_mapping                  = var.attribute_mapping
        attribute_condition                = var.attribute_condition
        oidc {
            issuer_uri        = var.issuer_uri
        }
    }
    ```
    - [code/models/terraform/auth/variable.tf](./code/models/terraform/auth/variable.tf)
    ```
    ...
    variable "attribute_mapping" {
        type = map(any)
        default = {
            "google.subject"                = "assertion.sub"
            "attribute.aud"                 = "assertion.aud"
            "attribute.repository_owner"    = "assertion.repository_owner"
        }
    }

    variable "attribute_condition" {
        type    = string
        default = <<EOT
            assertion.repository_owner == "patcha-ranat"
        EOT
    }

    variable "issuer_uri" {
        type    = string
        default = "https://token.actions.githubusercontent.com"
    }
    ...
    ```

In the last step, we have to grant additional access to the service account which is quite hard to execute via web-based UI.
```bash
gcloud iam service-accounts add-iam-policy-binding "${SERVICE_ACC_NAME}@${PROJECT}.iam.gserviceaccount.com" \
  --project=${PROJECT_ID} \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://${IAM_PRINCIPAL_ID}/attribute.repository_owner/patcha-ranat"
```
*Note:*
- *For UI approach, you have to grant access via WIF pool page, on the right panel with 'CONNECTED SERVICE ACCOUNTS' tabs*
- `IAM_PRICIPAL_ID` is retrieved from WIF pool page, also you have to replace *'pricipal'* to *'principalSet'*.

However, there's some constraints for WIF that's worth mentioning
- Assertion(s) in `attribute_condition` must be specified as subset of `attribute_mapping`. We don't have to specify condition for every mapped assertions, but recommendation from official GCP documentation is that we should specify 1 assertion atleast for security purpose.
- Although there're example to specify multiple conditions as a string of `attribute_condition` like the below code snippet, there's a problem when we're trying to grant service account an IAM access. `--member` argument don't accept multiple conditions pattern. Some of specific project example, instead use `assertion.full = "assertion.A+assertion.B+..."` for fine grained controls to allow access to specific service accounts from specific events on specific GH repo.
    ```
    variable "attribute_condition" {
        type    = string
        default = <<EOT
            assertion.sub == "xxx"
            assertion.aud == "xxx"
            assertion.repository_owner == "patcha-ranat"
            ...
        EOT
    }
    ```
    Instead for `assertion.full`
    ```
    attribute_mapping = {
        "google.subject" = "assertion.sub"
        "attribute.aud"  = "assertion.aud"
        "attibute.full"  = "assertion.repository+assertion.+repository_owner+..."
    }
    ```
    ```bash
    principalSet://${IAM_PRINCIPAL_ID}/attribute.full/${GH_REPO}${GH_REPO_OWENER}...
    ```
- `issuer_uri` is a static URL obtained from example and mentioned in documentation from GitHub

**References:**
- How to use `assertion.full`: [Stack Overflow](https://stackoverflow.com/a/76451745)
- Another example of `assertion.full`: [Stack Overflow](https://stackoverflow.com/questions/72752410/attribute-mappings-in-configuring-workload-identity-federation-between-gcp-and-g)

#### Workload Identity Federation Debugging
```
# Error: 1

Error: google-github-actions/auth failed with: failed to generate Google Cloud federated token for //iam.googleapis.com/***: {"error":"invalid_request","error_description":"Invalid value for \"audience\". This value should be the full resource name of the Identity Provider
```
1. `GCP_WORKLOAD_IDENTITY_PROVIDER` in CD workflow must be in format: "project/<project_id>/..." with uri prefix removed.
    - [Solution Source - Stack Overflow](https://stackoverflow.com/questions/76146054/gitlab-ci-cd-fails-to-connect-with-gcp-using-workload-identity-federation-and-id)
```
# Error: 2

denied: Unauthenticated request. Unauthenticated requests do not have permission "artifactregistry.repositories.uploadArtifacts" on resource
```
2. `gcloud auth configure-docker` is required in CD workflow steps.
    - [Solution Source - Stack Overflow](https://stackoverflow.com/questions/75840164/permission-artifactregistry-repositories-uploadartifacts-denied-on-resource-usin)
```
# Error: 3

ERROR: (gcloud.auth.docker-helper) There was a problem refreshing your current auth tokens: ('Unable to acquire impersonated credentials'...
```
3. Granting additional iam access to service account specific for WIF is required
    ```bash
    gcloud iam service-accounts add-iam-policy-binding ...
    ```

```
# Error: 4

OIDC error: 403 'Unable to acquire impersonated credentials' [principalSet mismatch with the Subject claim]
```
- Attribute conditions specified when first creating WIF provider are not matched with conditions that we grant to Service Account in the last step.
    - [Solution Source- Stack Overflow](https://stackoverflow.com/a/76451745)


Finally, you can now manual trigger workflow for automated deployment (CD Workflow)

*References:*
1. **How OIDC work with cloud provider behind the scene, JWT attributes, and advance configuration**: [About security hardening with OpenID Connect](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
2. **Official GHA with GCP on Github Repo**: [Authenticate to Google Cloud from GitHub Actions - Direct Workload Identity Federation](https://github.com/google-github-actions/auth?tab=readme-ov-file#preferred-direct-workload-identity-federation)
3. **GHA steps for WIF, recommendation, and gcloud commands from official published article**: [Enabling keyless authentication from GitHub Actions - Google Cloud Platform](https://cloud.google.com/blog/products/identity-security/enabling-keyless-authentication-from-github-actions)
4. WIF & Terraform Medium Example: [Workload Identity Federation & GitHub Actions & Terraform - Medium](https://articles.arslanbekov.com/workload-identity-federation-github-actions-terraform-684813c201a9)
5. GitHub default variables: [Store information in variables](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#default-environment-variables)

For more resource for deployment overview, I recommended this [ML Deployment Chapter](https://github.com/alexeygrigorev/mlbookcamp-code/tree/master/course-zoomcamp/05-deployment) from [*Machine Learning Zoomcamp*](https://github.com/alexeygrigorev/mlbookcamp-code/tree/master).

## 7. Conclusion

From this project, we learned how to:
- **Design data architecture, and select tools for each process** to be used in the project.
- **Set up environment for virtualization** to simulate the local environment such as database, and webserver.
- **Create an ETL pipeline** to extract data from various sources, transform the data, and load the data to the target database.
- **Utilize cloud services** to extend the datalake, data warehouse to production.
- **Create a dashboard** to visualize the data and analyze the business.
- **Develop machine learning models** to predict the future sales, customer segments, and inferencing customer buying behavior.
- **Deploy the model to production** to leverage the business using API web service, and cloud services.

This is the biggest personal project I've ever done so far, and I learned a lot from it. I hope it can be useful for anyone who shares the same learning path. Although this project is not fully finished yet, but I will keep working on it and update it continuously as my knowledge and experience grow.

***Thank you for your reading, happy learning.***

---
*What's coming next?*

- Recommendation System, Churn prediction Model, and Price Analysis.

---