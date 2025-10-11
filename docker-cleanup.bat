@echo off
echo Cleaning up Docker containers...
FOR /F "tokens=*" %%i IN ('docker ps -aq') DO docker rm -f %%i

echo Cleaning up Docker images...
FOR /F "tokens=*" %%i IN ('docker images -q') DO docker rmi -f %%i

echo Cleaning up Docker volumes...
FOR /F "tokens=*" %%i IN ('docker volume ls -q') DO docker volume rm %%i

echo Cleaning up Docker networks (excluding default ones)...
FOR /F "tokens=*" %%i IN ('docker network ls --format "{{.Name}}"') DO (
    IF /I NOT "%%i"=="bridge" IF /I NOT "%%i"=="host" IF /I NOT "%%i"=="none" docker network rm %%i
)

echo Performing final system prune...
docker system prune -a -f

echo Docker cleanup complete.
pause