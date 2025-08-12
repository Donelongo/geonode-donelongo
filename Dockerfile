# ---- Stage 1: Build React App ----
# This stage uses a Node.js image to build your frontend.
# It's a temporary stage that will be discarded later.
FROM node:18-alpine AS builder

# Set the working directory for the frontend build
WORKDIR /usr/src/app/frontend
COPY ./agro-climate-advisory-system-frontend/package*.json ./
RUN npm install --legacy-peer-deps
COPY ./agro-climate-advisory-system-frontend/ ./
RUN npm run build


# ---- Stage 2: Build The Final GeoNode App ----
# This is your original Dockerfile, which now starts here.
FROM geonode/geonode-base:latest-ubuntu-22.04
LABEL GeoNode development team

# Ensure the target directory exists in the container
RUN mkdir -p /usr/src/my_geonode

# Install system dependencies
RUN apt-get update -y && \
    apt-get install -y \
    curl wget unzip gnupg2 locales \
    libjpeg-dev zlib1g-dev libfreetype6-dev libpng-dev libxml2-dev libxslt1-dev \
    build-essential

# Configure locales
RUN sed -i -e 's/# C.UTF-8 UTF-8/C.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

# Set PIP environment variables
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=10
ENV PIP_NO_CACHE_DIR=off

# Add /usr/src to PYTHONPATH
ENV PYTHONPATH=/usr/src:${PYTHONPATH}

# Copy the core Django project
COPY src/my_geonode /usr/src/my_geonode/

# <<-- THE MAGIC STEP -->>
# Create the target directory for the frontend build
RUN mkdir -p /usr/src/my_geonode/static/frontend
# Copy the built React app FROM THE 'builder' STAGE into your GeoNode static files
COPY --from=builder /usr/src/app/frontend/build /usr/src/my_geonode/static/frontend/

# Expose media assets also at /static/media (some CRA bundles resolve to /static/media/*)
RUN if [ -d /usr/src/my_geonode/static/frontend/static/media ]; then \
    mkdir -p /usr/src/my_geonode/static/media && \
    cp -r /usr/src/my_geonode/static/frontend/static/media/* /usr/src/my_geonode/static/media/; \
    echo "Duplicated CRA media assets to /usr/src/my_geonode/static/media"; \
    fi

# Set working directory
WORKDIR /usr/src/my_geonode

# Copy remaining project files and scripts
COPY src/tasks.py .
COPY src/entrypoint.sh .
COPY src/manage.py .
COPY src/requirements.txt .
COPY src/wait-for-databases.sh /usr/bin/wait-for-databases
COPY src/celery.sh /usr/bin/celery-commands
COPY src/celery-cmd /usr/bin/celery-cmd
COPY src/uwsgi.ini /usr/src/my_geonode/uwsgi.ini

# Set execute permissions
RUN chmod +x tasks.py \
    && chmod +x entrypoint.sh \
    && chmod +x manage.py \
    && chmod +x /usr/bin/wait-for-databases \
    && chmod +x /usr/bin/celery-commands \
    && chmod +x /usr/bin/celery-cmd

# Install Python dependencies
RUN yes w | pip install --upgrade pip && \
    yes w | pip install --src /usr/src -r requirements.txt

# Install other Python packages
RUN yes w | pip install django-cors-headers
RUN yes w | pip install reportlab

# Cleanup
RUN apt-get autoremove --purge -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Export ports
EXPOSE 8000