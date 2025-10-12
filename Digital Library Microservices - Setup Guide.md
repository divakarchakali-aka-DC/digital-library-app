# Digital Library Microservices - Setup Guide

## Prerequisites

- Docker installed on your system
- Docker Compose installed
- Git installed
- At least 2GB of free disk space
- Ports 5000, 5001, 5002, 5003, and 3306 available

## Step 1: Clone the Repository

```bash
# Clone the repository
git clone <repository-url>
cd digital-library

# Verify the project structure
ls -la
```

## Expected structure:

```
digital-library/
├── Dockerfile               # Multi-stage build for main application
├── docker-compose.yml       # Multi-service orchestration
├── app.py                   # Main Flask application (Web Gateway)
├── requirements.txt         # Python dependencies for main app
├── .env                     # Environment variables (create this file)
|
├── auth/                    # Authentication microservice
│   ├── auth_service.py      # JWT & user management
│   ├── Dockerfile           # Container configuration
│   └── requirements.txt     # Python dependencies
|
├── book/                    # Book management microservice  
│   ├── book_service.py      # Book CRUD operations
│   ├── Dockerfile           # Container configuration
│   └── requirements.txt     # Python dependencies
|
├── borrow/                  # Borrowing microservice
│   ├── borrow_service.py    # Borrow/return logic
│   ├── Dockerfile           # Container configuration
│   └── requirements.txt     # Python dependencies
|
├── database/                # MySQL database setup
│   ├── database.sql         # Schema & initial data
│   ├── init.sh              # Database initialization
│   ├── my.cnf               # MySQL configuration
│   └── Dockerfile           # Database container
|
└── templates/               # HTML templates
    ├── base.html            # Base template with navigation
    ├── signin.html          # User login page
    ├── signup.html          # User registration page
    ├── books.html           # Book listing with search
    ├── book_details.html    # Individual book details page
    ├── borrow.html          # User's borrowed books page
    ├── admin.html           # Admin dashboard
    ├── admin-users.html     # User management page
    ├── add-book.html        # Add new book form
    └── edit-book.html       # Edit existing book form
```

## Step 2: Environment Configuration

Create a `.env` file in the project root:

```bash
# Create .env file
cat > .env << EOF
# Database Configuration
DB_HOST=db
DB_PORT=3306
DB_NAME=digital_library
DB_USER=app_user
DB_PASSWORD=secretpassword

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-prod

# Note: DB_PASSWORD is used for both MariaDB root (admin) and app_user (services)
EOF
```

**Important**: For production, change the `JWT_SECRET` and `DB_PASSWORD` to strong, unique values.

## Step 3: Build and Start Services

```bash
# Build and start all services in detached mode
docker-compose up -d --build

# Alternative: Build first, then start
docker-compose build --no-cache
docker-compose up -d

# Build and start specific service in detached mode
docker-compose up -d --build

# Alternative: Build first, then start
docker-compose build --no-cache db
docker-compose up -d db
```

## Step 4: Verify Services are Running

### Check Container Status
```bash
# Check all containers status
docker-compose ps

# Expected output:
# Name                      Command               State           Ports
# digital-library-app-1     ...                   Up              0.0.0.0:5000->5000/tcp
# digital-library-auth-1    ...                   Up              5002/tcp
# digital-library-book-1    ...                   Up              5001/tcp
# digital-library-borrow-1  ...                   Up              5003/tcp
# digital-library-db-1      ...                   Up              0.0.0.0:3306->3306/tcp
```

### Check Container Logs
```bash
# Check logs for all services
docker-compose logs

# Check logs for specific service
docker-compose logs app
docker-compose logs db
docker-compose logs auth

# Follow logs in real-time
docker-compose logs -f app
```

### Verify Service Health
```bash
# Check if web application is responding
curl http://localhost:5000

# Check individual services (from within the network)
docker-compose exec app curl -s http://auth-service:5002/health
```

## Step 5: Validate Database Setup

### Connect to Database
```bash
# Connect to MySQL database
docker-compose exec db mysql -u <DB_USER from .env> -psecretpassword <DB_PASSWORD from .env file>

# Once connected, run these SQL commands:
```

### Verify Database Structure
```sql
-- Check if database and tables are created
SHOW DATABASES;
USE digital_library;
SHOW TABLES;

-- Expected tables: users, books, borrows

-- Check books data
SELECT id, title, author, available FROM books;

-- Check users data (should have admin user)
SELECT id, username, role FROM users;

-- Exit MySQL
EXIT;
```

### Expected Initial Data
- **Books**: 17 pre-loaded books (14 DevOps + 3 classics)
- **Users**: 1 admin user (admin/adminpass)
- **Borrows**: Empty initially

## Step 6: Access the Application

1. **Open your browser** and go to: `http://localhost:5000`

2. **Initial Login**:
   - Username: `admin`
   - Password: `adminpass`

3. **Test Basic Functions**:
   - Browse books
   - Search for books
   - View book details
   - Borrow a book
   - Check "My Borrowed Books"

## Troubleshooting Common Issues

### Issue 1: Containers Not Starting

**Symptoms**: `docker-compose ps` shows containers as "Exited" or "Restarting"

**Solutions**:
```bash
# Check specific service logs
docker-compose logs app
docker-compose logs db

# Restart specific service
docker-compose restart app

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Issue 2: Database Connection Errors

**Symptoms**: "Can't connect to MySQL server" in logs

**Solutions**:
```bash
# Check if database container is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Wait for database to initialize (can take 30-60 seconds on first run)
sleep 30

# Test database connection manually
docker-compose exec db mysql -u <DB_USER from .env> -psecretpassword <DB_PASSWORD from .env file> -e "SHOW TABLES;"
```

### Issue 3: Port Already in Use

**Symptoms**: "Bind for 0.0.0.0:5000 failed: port is already allocated"

**Solutions**:
```bash
# Check what's using the port
netstat -tulpn | grep :5000

# Stop the conflicting service or
# Change ports in docker-compose.yml and restart
```

### Issue 4: Application Not Accessible

**Symptoms**: Browser shows "Connection refused" or timeout

**Solutions**:
```bash
# Check if app container is running
docker-compose ps app

# Check app logs for errors
docker-compose logs app

# Test from inside the container
docker-compose exec app curl http://localhost:5000
```

### Issue 5: Missing Dependencies

**Symptoms**: Python import errors in logs

**Solutions**:
```bash
# Rebuild the containers
docker-compose down
docker-compose up -d --build

# Check requirements files exist
ls auth/requirements.txt book/requirements.txt borrow/requirements.txt
```

## Validation Checklist

### Container Validation
```bash
# All containers should be running
docker-compose ps

# All services should respond internally
docker-compose exec app ping -c 1 auth-service
docker-compose exec app ping -c 1 book-service
```

### Database Validation
```bash
# Database should be accessible
docker-compose exec db mysql -u <DB_USER from .env> -psecretpassword <DB_PASSWORD from .env file> -e "SHOW DATABASES;"

# Should have initial data
docker-compose exec db mysql -u <DB_USER from .env> -psecretpassword <DB_PASSWORD from .env file> -e "SELECT COUNT(*) as book_count FROM books;"
```

### Application Validation
```bash
# Web interface should be accessible
curl -I http://localhost:5000

# API services should respond
curl http://localhost:5000/books
```

### Functional Validation
1. **Login** with admin credentials
2. **Browse** books and use search
3. **Borrow** a book
4. **Return** the borrowed book
5. **Admin functions** (if logged in as admin)

## Maintenance Commands

### Regular Operations
```bash
# Stop all services
docker-compose down

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Update and rebuild
git pull
docker-compose down
docker-compose up -d --build
```

### Cleanup
```bash
# Remove all containers, volumes, and networks
docker-compose down -v

# Remove all Docker images for this project
docker-compose down --rmi all
```

### Backup Database
```bash
# Create database backup
docker-compose exec db mysqldump -u app_user -psecretpassword digital_library > backup.sql

# Restore from backup
docker-compose exec -T db mysql -u app_user -psecretpassword digital_library < backup.sql
```

## Support

If you encounter issues not covered in this guide:

1. Check all service logs: `docker-compose logs`
2. Verify environment variables in `.env` file
3. Ensure Docker has enough resources (memory, disk space)
4. Check Docker daemon is running: `docker info`

For persistent issues, check the project documentation or create an issue in the repository.
