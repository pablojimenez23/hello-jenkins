FROM jenkins/jenkins:lts-jdk17
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends docker-cli \
 && rm -rf /var/lib/apt/lists/*
