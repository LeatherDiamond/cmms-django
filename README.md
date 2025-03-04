# Navigation
* ***[Project description](#project-description)***
    * ***[Overview](#overview)***
    * ***[Key features](#key-features)***
    * ***[Technicak stack](#technical-stack)***
    * ***[Project structure](#project-structure)***
    * ***[Interaction flow](#interaction-flow)***
    * ***[Diagram](#diagram)***
* ***[How to start locally](#how-to-start-locally)***
* ***[How to start with Docker](#how-to-start-with-docker)***
* ***[Code formatting and quality checking tools](#code-formatting-and-quality-checking-tools)***
* ***[Pipeline configuration](#pipeline-configuration)***
* ***[Running tests inside the container](#running-tests-inside-the-container)***
* ***[Runing tests locally](#running-tests-locally)***
* ***[Running tests with pipeline](#running-tests-with-pipeline)***
* ***[Why should you try it](#why-should-you-try-it)***
* ***[License](#license)***

# Project description

## Overview

The CMMS (Computerized Maintenance Management System) project is a comprehensive web-based application designed to streamline and manage maintenance tasks within an organization. Built using Django, this system provides a robust platform for task management, user management, and reporting. The CMMS project features a fully responsive design, ensuring an optimized user experience across both desktop and mobile devices. The interface dynamically adapts to different screen sizes, offering a mobile-friendly layout with intuitive navigation and task views. The primary goal is to enhance the efficiency of maintenance operations by providing a centralized system for tracking tasks, managing user roles, and generating insightful reports.

## Key features

**1. Task Management:**
* ***Create, update, and delete tasks.***
* ***Assign tasks to multiple users.***
* ***Set deadlines, priorities, and categories for tasks.***
* ***Attach files to tasks for better documentation.***

**2. User Management:**
* ***Role-based access control with permissions for different user roles.***
* ***User authentication and authorization.***
* ***Password management including reset and change functionalities.***

**3. Reporting and Analytics:**
* ***Generate reports on task status, user performance, and maintenance trends.***
* ***Visualize data through charts and graphs.***

**4. Notifications:**
* ***Email notifications for task assignments, updates, and comments.***
* ***Configurable email settings for different environments.***

**5. File Management:**
* ***Upload and manage attachments for tasks.***
* ***Serve attachments securely from the media directory.***

**6. Localization:**
* ***Support for multiple languages.***
* ***Configurable locale settings.***

## Technicak stack

- **Backend:** Python *3.11.3,* Django *5.1.4*
- **Frontend:** HTML, CSS, JavaScript, jQuery, Bootstrap
- **Database:** SQLite (default), configurable for other databases
- **Authentication:** Custom authentication backend, Argon2 password hashing
- **Deployment:** Docker, Docker Compose
- **Testing:** Pytest, pytest-django, pytest-mock, freezegun

## Project structure

The project is organized into several key directories and files:

- **src/**: Contains the main application code.
    - **buildings/**: Manages building-related data.
    - **homepage/**: Handles the main page view.
    - **tasks/**: Manages tasks, including models, views, and migrations.
    - **users/**: Manages user data and authentication.
    - **static/**: Contains static files like CSS, JavaScript, and images.
    - **templates/**: Contains HTML templates for rendering views.
    - **tests/**: Contains test cases for various components of the application.
    - **manage.py**: Django's command-line utility for administrative tasks.
    - **proj/**: Contains project settings, URLs, and WSGI/ASGI configurations.
- **.env.sample**: Example of mandatory environment variables that should be configured in `.env` file.
- **.gitlab-ci.yml**: Pipeline configuration file.
- **.entrypoint.sh**: Executable script to start the project in docker container.
- **run-test.sh**: Executable sript to run tests. Used in pipeline.
- **.flake8**: Flake8 configuration file.
- **.gitattributes**: Git attributes file.
- **.gitignore**: Git ignore file.
- **.dockerignore**: Docker ignore file.
- **Dockerfile**: Docker configuration for building the application image.
- **docker-compose.yml**: Docker Compose configuration for setting up the development environment.
- **pyproject.toml**: Configuration for Poetry, the dependency management tool.
- **README.md**: Project documentation.

## Interaction flow

**1. User Authentication:**
* ***Users log in using their email and password.***
* ***Role-based access control ensures users have appropriate permissions.***

**2. Task Management:**
* ***Users create tasks and assign them to relevant personnel.***
* ***Tasks can have attachments, deadlines, priorities, and categories.***
* ***Users can update task status and leave comments.***

**3. Notifications:**
* ***Email notifications are sent for task assignments, updates, and comments.***
* ***Configurable email settings ensure notifications are sent appropriately.***

**4. Reporting:**
* ***Users can generate reports on task status, user performance, and maintenance trends.***
* ***Data is visualized through charts and graphs for better insights.***

## Diagram

![Diagram]()

# How to start locally

1. Clone current repository to your local machine:
```
https://github.com/LeatherDiamond/cmms-django.git
```
2. Navigate to the root directory of the project;
3. Configure `.env` file by assigning values to the variables defined in `.env.sample`;
4. Make sure that [Gettext](https://www.gnu.org/software/gettext/) is installed on your local machine;
5. Activate virtual environment:
```
poetry shell
```
6. Install all dependencies:
```
poetry install
```
7. Apply all migrations:
```
python manage.py migrate
```
8. Create a superuser to provide future access to django admin panel:
```
python manage.py createsuperuser
```
9. Run development server:
```
python manage.py runserver
```
After completing all the steps, the project will be launched and available at `http://localhost:8000/`.

# How to start with Docker

1. Install [Docker](https://docs.docker.com/engine/install/) on your local machine, if it wasn't done yet, and launch it;
2. Clone current repository to your local machine:
 ```
https://github.com/LeatherDiamond/cmms-django.git
 ```
3. Configure `.env` file by assigning values to the variables defined in `.env.sample`;
4. USe the command to build and start the container:
```
docker compose up --build
```
After completing all the steps, the project will be launched and available at `http://localhost:8000/`. 

# Code formatting and quality checking tools
> ###### **NOTE:**
> Note, that autolaunch of code quality checking and formatting tools is already included in ***Gitlab*** and ***Github*** pipelines configuration files.
1. Run `poetry shell` to activate environment if it's not active yet;
2. Run `black . --check` to check if the code needs to be reformatted;
3. Run `black .` to reformat the code;
4. Run `flake8` to identify potential issues, such as syntax errors, code style violations, and other coding inconsistencies during the development process;

# Pipeline configuration
> ###### NOTE: 
> To provide correct work of the pipeline, please configure neccessary `REPOSITORY SECRETS` that are mandatory in configuration files.
> Also note that if you are using a **GitLab** you should configure a [GitLab Runner](https://docs.gitlab.com/runner/install/), and depending on its configuration, you may need
> [Docker](https://docs.docker.com/engine/install/) launched locally. For example, if your Runner is configured for local Docker setup, you will need to launch Docker on your 
> machine for the pipeline to work correctly because the GitLab pipeline uses [Docker-in-Docker](https://docs.gitlab.com/ee/ci/docker/using_docker_build.html).

The project includes configured pipeline files for [GitLab]() and [GitHub](), ensuring that each new code push triggers the build and launch of the project container, runs tests within the container, and subsequently stops it, providing continuous quality code delivery. No matter where your project is stored: `GitHub` or `GitLab`, thanks to configured files the pipeline will be launched automatically.

# Running tests locally

1. Make sure that points `1 - 7` from ***[How to start locally](#how-to-start-locally)*** section are already completed;
2. Launch tests with the command:
```
pytest
```

# Running tests inside the container

1. Make sure that `all the points` from ***[How to start with Docker](#how-to-start-with-docker)*** section are already completed;
2. Enter the `cmms.webapp` container with the command:
```
docker exec -it cmms.webapp bash
```
3. After you entered the container, launch tests with te command:
```
pytest
```

# Running tests with pipeline

Pipeline configuration files are already set to launch tests automatically. It means that each new code push triggers the build and launch of the project container, runs tests within the container, and subsequently stops it.
> ###### NOTE:
> Take a look at the ***[Pipeline configuration](#pipeline-configuration)*** section for some important notes.

# Why should you try it

The CMMS project is a powerful tool designed to enhance the efficiency of maintenance operations within an organization. With its comprehensive task management features, robust user management, and insightful reporting capabilities, it provides a centralized platform for managing all maintenance-related activities. The use of modern technologies and best practices ensures the system is secure, scalable, and easy to use.
