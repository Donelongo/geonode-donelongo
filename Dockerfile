FROM geonode/geonode-base:latest-ubuntu-22.04
LABEL GeoNode development team

# Ensure the target directory exists in the container
RUN mkdir -p /usr/src/my_geonode

# Install system dependencies (including new ones for reportlab)
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

# Set PIP environment variables for better download resilience
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=10
ENV PIP_NO_CACHE_DIR=off

# Add /usr/src to PYTHONPATH so Python can find 'my_geonode' as a module
ENV PYTHONPATH=/usr/src:${PYTHONPATH}

# Copy the core Django project (my_geonode and its apps like info_hub)
# from host's src/my_geonode to container's /usr/src/my_geonode
COPY src/my_geonode /usr/src/my_geonode/

# Set working directory inside the container to the project root
WORKDIR /usr/src/my_geonode

# Copy individual scripts from host's src/ directory to the container's WORKDIR (./ = /usr/src/my_geonode)
COPY src/tasks.py .
COPY src/entrypoint.sh .
COPY src/manage.py .
COPY src/requirements.txt .

# Copy global utility scripts to /usr/bin/ with their intended names
COPY src/wait-for-databases.sh /usr/bin/wait-for-databases
COPY src/celery.sh /usr/bin/celery-commands
COPY src/celery-cmd /usr/bin/celery-cmd


COPY src/uwsgi.ini /usr/src/my_geonode/uwsgi.ini


# Set execute permissions for all necessary scripts
RUN chmod +x tasks.py \
    && chmod +x entrypoint.sh \
    && chmod +x manage.py \
    && chmod +x /usr/bin/wait-for-databases \
    && chmod +x /usr/bin/celery-commands \
    && chmod +x /usr/bin/celery-cmd

# Install Python dependencies from requirements.txt
# Upgrade pip first to get better download resilience
RUN yes w | pip install --upgrade pip && \
    yes w | pip install --src /usr/src -r requirements.txt

# --- ADD THIS NEW RUN COMMAND FOR REPORTLAB ---
RUN yes w | pip install reportlab
# -----------------------------------------------

# This line is for debugging, keep it for now.
RUN pip show reportlab

# Install "geonode-contribs" apps (if uncommented in your original, keep it. Otherwise, leave commented)
# RUN cd /usr/src; git clone https://github.com/GeoNode/geonode-contribs.git -b master
# Install logstash and centralized dashboard dependencies (if uncommented in your original, keep it. Otherwise, leave commented)
# RUN cd /usr/src/geonode-contribs/geonode-logstash; pip install --upgrade   -e . \
#     cd /usr/src/geonode-contribs/ldap; pip install --upgrade   -e .

# Cleanup apt update lists
RUN apt-get autoremove --purge -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Export ports
EXPOSE 8000

# We provide no command or entrypoint as this image can be used to serve the django project or run celery tasks
# ENTRYPOINT /usr/src/my_geonode/entrypoint.sh