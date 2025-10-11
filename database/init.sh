#!/bin/bash
set -e

# Wait for MariaDB to start and be ready (using root)
echo "Waiting for MariaDB to start..."
while ! mysqladmin ping -h"localhost" -u"root" -p"${MARIADB_ROOT_PASSWORD}" --silent; do
    echo 'Waiting for MariaDB...'
    sleep 2
done

# Explicitly create database if not exists (backup for MARIADB_DATABASE)
mysql -u root -p"${MARIADB_ROOT_PASSWORD}" -e "CREATE DATABASE IF NOT EXISTS ${MARIADB_DATABASE};"

# Create app_user if not exists and grant privileges (avoids root for apps)
mysql -u root -p"${MARIADB_ROOT_PASSWORD}" -e "
CREATE USER IF NOT EXISTS '${MARIADB_USER}'@'%' IDENTIFIED BY '${MARIADB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${MARIADB_DATABASE}.* TO '${MARIADB_USER}'@'%';
FLUSH PRIVILEGES;
"

echo "Database '${MARIADB_DATABASE}' initialized with user '${MARIADB_USER}' ready."