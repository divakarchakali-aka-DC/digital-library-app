FROM mariadb:10.6
COPY my.cnf /etc/mysql/conf.d/
COPY init.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/init.sh  # Ensure executable
COPY database.sql /docker-entrypoint-initdb.d/