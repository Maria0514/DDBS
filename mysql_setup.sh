#!/bin/bash
# Setup two MySQL instances
docker run -d --name mysql1 -e MYSQL_ROOT_PASSWORD=password -p 3306:3306 mysql:8.4
docker run -d --name mysql2 -e MYSQL_ROOT_PASSWORD=password -p 3307:3306 mysql:8.4