FROM python:3.11.3-slim
ARG group

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt install --no-install-recommends --yes curl gnupg2 gettext

# Creating a new user, upgrading pip to the latesr version and installing poetry
RUN useradd -ms /bin/bash newuser && \
    python -m pip install --upgrade pip && \
    pip install poetry

# Copy pyproject.toml and poetry.lock to install dependencies
WORKDIR /src
COPY pyproject.toml poetry.lock ./

# Installing dependencies to system python
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction $group

# Сopy the remaining files
COPY . .

# Change ownership of the database file and directory
RUN chown -R newuser:newuser /src

# Runing the file as an executable script
RUN chmod +x entrypoint.sh

# Changing user 
USER newuser

# Launching the script
ENTRYPOINT [ "./entrypoint.sh" ]

# Checking health status
HEALTHCHECK --interval=3s --timeout=10s --start-period=15s --retries=5 \
  CMD curl -f http://webapp:8000/admin/login/?next=/admin/ || exit 1