# Digital Library Microservices — **Docker Stack (Swarm) Setup Guide**

## Prerequisites

* Docker installed and configured
* Docker Swarm initialized (single or multi-node)
* Git installed
* At least **2GB** free disk space
* Ports **5000, 5001, 5002, 5003, and 3306** available

> 💡 Tip: Run this on your Swarm **manager node**, as only managers can deploy stacks.

---

## Step 1: Initialize Docker Swarm

If Swarm is not yet initialized on your system, do this first:

```bash
docker swarm init
```

If you already have a Swarm, verify it with:

```bash
docker info | grep Swarm
```

Expected output:

```
Swarm: active
```

---

## Step 2: Clone the Repository

```bash
git clone <repository-url>
cd digital-library
```

Verify project structure:

```
digital-library/
├── docker-stack.yml          # Stack definition (for Swarm)
├── Dockerfile                # Multi-stage build for main app
├── .env                      # Environment variables
├── auth/                     # Authentication microservice
├── book/                     # Book microservice
├── borrow/                   # Borrowing microservice
├── database/                 # MySQL setup
└── templates/                # Web templates
```

---

## Step 3: Configure Environment Variables

Create a `.env` file in the project root if it doesn’t exist:

```bash
cat > .env << EOF
# Database Configuration
DB_HOST=db
DB_PORT=3306
DB_NAME=digital_library
DB_USER=app_user
DB_PASSWORD=secretpassword

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-prod
EOF
```

> ⚠️ **Important:**
> `.env` files are **not automatically loaded** by `docker stack deploy`.
> You must **export** the variables into your current shell **before** deploying.

---

## Step 4: Export Environment Variables

Run the following on your **manager node** before deployment:

```bash
set -a
source .env
set +a
```

Verify they’re available:

```bash
env | grep DB_
env | grep JWT_SECRET
```

You should see your values listed.

---

## Step 5: Deploy the Stack

Deploy all services using your stack file:

```bash
docker stack deploy -c docker-stack.yml digital-library
```

Verify stack creation:

```bash
docker stack ls
docker stack services digital-library
```

Example output:

```
NAME                SERVICES
digital-library     5
```

---

## Step 6: Verify Service Health

### Check service status

```bash
docker service ls
```

Expected output:

```
ID      NAME                         MODE        REPLICAS   IMAGE
x1234   digital-library_app           replicated  2/2        digital-library:latest
x2345   digital-library_auth          replicated  1/1        auth:latest
x3456   digital-library_book          replicated  1/1        book:latest
x4567   digital-library_borrow        replicated  1/1        borrow:latest
x5678   digital-library_db            replicated  1/1        mysql:latest
```

### Inspect running containers

```bash
docker ps
```

### View service logs

```bash
docker service logs digital-library_app --tail 50
docker service logs digital-library_db --tail 50
```

---

## Step 7: Validate Database Setup

Connect to the running DB container:

```bash
docker exec -it $(docker ps --filter "name=digital-library_db" -q) mysql -u app_user -psecretpassword digital_library
```

Check structure:

```sql
SHOW TABLES;
SELECT id, title, author, available FROM books;
SELECT id, username, role FROM users;
```

---

## Step 8: Access the Application

Open in your browser:

```
http://<manager-node-ip>:5000
```

Default login credentials:

* **Username:** `admin`
* **Password:** `adminpass`

Test core workflows:

* Sign in → Browse → Borrow → Return → Admin Panel

---

## Step 9: Stack Management Commands

### Check all services

```bash
docker stack ps digital-library
```

### Update the stack (after code changes)

```bash
set -a
source .env
set +a
docker stack deploy -c docker-stack.yml digital-library
```

### Remove the stack

```bash
docker stack rm digital-library
```

---

## Step 10: Troubleshooting

### 1. Environment Variables Not Applied

**Symptom:** Containers can’t access DB or JWT secrets.

**Fix:**

```bash
set -a
source .env
set +a
docker stack deploy -c docker-stack.yml digital-library
```

> Don’t rely on `env_file:` in stack YAML — it’s ignored by Swarm.

---

### 2. Service Failing to Start

```bash
docker service ps digital-library_app
docker service logs digital-library_app
```

Re-deploy:

```bash
docker stack rm digital-library
docker stack deploy -c docker-stack.yml digital-library
```

---

### 3. Database Connection Errors

**Cause:** DB initialization delay.
**Fix:** Wait ~30 seconds before app tries connecting.

---

### 4. Scaling Services

```bash
docker service scale digital-library_app=3
```

Check replicas:

```bash
docker service ls
```

---

### 5. Removing Unused Resources

```bash
docker system prune -af
```

---

## Step 11: Validation Checklist

| Validation Area | Command                                 | Expected                |
| --------------- | --------------------------------------- | ----------------------- |
| Stack           | `docker stack ls`                       | Stack deployed          |
| Services        | `docker service ls`                     | All replicas 1/1 or 2/2 |
| Database        | `SHOW TABLES;`                          | Tables exist            |
| App Access      | Browser or `curl http://localhost:5000` | Page loads successfully |

---

## Step 12: Optional — Multi-Node Deployment

If you want to run this across multiple nodes:

1. On manager:

   ```bash
   docker swarm init
   ```

   Copy the join token from output.

2. On each worker node:

   ```bash
   docker swarm join --token <token> <manager-ip>:2377
   ```

3. Re-deploy the stack; Docker Swarm will automatically distribute services.

---

## Maintenance Commands

```bash
# View all nodes
docker node ls

# View stack details
docker stack ps digital-library

# Remove stack
docker stack rm digital-library

# Redeploy after code changes
set -a; source .env; set +a
docker stack deploy -c docker-stack.yml digital-library
```

---

## Summary

| Compose Version        | Swarm Version             |
| ---------------------- | ------------------------- |
| `docker-compose.yml`   | `docker-stack.yml`        |
| `env_file:` works      | Ignored                   |
| Local orchestration    | Distributed orchestration |
| Simple restart policy  | Advanced rolling updates  |
| `docker-compose up -d` | `docker stack deploy -c`  |
