# MySQL Database Setup Guide

This guide will walk you through setting up the MySQL database for Job Workspace.

## Prerequisites
- MySQL Server installed on your system
- MySQL Workbench (recommended) or command-line MySQL client

## Step 1: Install MySQL (if not already installed)

### Windows:
1. Download MySQL Installer from: https://dev.mysql.com/downloads/installer/
2. Run the installer and choose "Developer Default" or "Server only"
3. Follow the installation wizard
4. Set a root password (remember this - you'll need it!)
5. Complete the installation

### macOS:
```bash
# Using Homebrew
brew install mysql
brew services start mysql
```

### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql
```

## Step 2: Open MySQL Workbench

1. Launch **MySQL Workbench** from your applications
2. You should see a connection named "Local instance MySQL" or similar
3. Click on it to connect
4. Enter your root password if prompted

## Step 3: Create the Database

### Option A: Using MySQL Workbench (GUI)

1. In MySQL Workbench, click on the **"SQL"** tab or press `Ctrl+Shift+Enter`
2. Type the following command:
   ```sql
   CREATE DATABASE IF NOT EXISTS job_workspace;
   ```
3. Click the **Execute** button (⚡) or press `Ctrl+Enter`
4. You should see "1 row(s) affected" in the output

### Option B: Using Command Line

1. Open Command Prompt (Windows) or Terminal (Mac/Linux)
2. Connect to MySQL:
   ```bash
   mysql -u root -p
   ```
3. Enter your root password when prompted
4. Run:
   ```sql
   CREATE DATABASE IF NOT EXISTS job_workspace;
   ```

## Step 4: Run the Schema SQL File

### Option A: Using MySQL Workbench (Recommended)

1. In MySQL Workbench, go to **File → Open SQL Script**
2. Navigate to your project folder: `Job Workspace/database/schema.sql`
3. Select the file and click **Open**
4. The SQL script will open in a new tab
5. Make sure the correct database is selected:
   - Look at the bottom toolbar
   - Click the dropdown next to the database icon
   - Select `job_workspace` (or type: `USE job_workspace;` in the SQL editor)
6. Click the **Execute** button (⚡) or press `Ctrl+Enter`
7. You should see multiple "OK" messages indicating successful execution

### Option B: Using Command Line

1. Open Command Prompt or Terminal
2. Navigate to your project directory:
   ```bash
   cd "D:\Assignment Works(Junior)\Job Workspace"
   ```
3. Run the SQL file:
   ```bash
   mysql -u root -p job_workspace < database/schema.sql
   ```
4. Enter your root password when prompted

### Option C: Copy-Paste Method

1. Open `database/schema.sql` in a text editor
2. Copy all the contents (Ctrl+A, Ctrl+C)
3. In MySQL Workbench, open a new SQL tab
4. Select the `job_workspace` database (or run `USE job_workspace;`)
5. Paste the SQL code (Ctrl+V)
6. Click **Execute** (⚡) or press `Ctrl+Enter`

## Step 5: Verify the Setup

1. In MySQL Workbench, expand the `job_workspace` database in the left sidebar
2. Click on **Tables**
3. You should see the following tables:
   - `users`
   - `job_posts`
   - `job_applications`
   - `reviews`
   - `messages`
   - `notifications`
   - `payments`

4. To verify data, run:
   ```sql
   USE job_workspace;
   SHOW TABLES;
   SELECT COUNT(*) FROM users;
   ```

## Step 6: Create Admin User

After setting up the database, create an admin user:

1. Open Command Prompt or Terminal
2. Navigate to the backend directory:
   ```bash
   cd "D:\Assignment Works(Junior)\Job Workspace\backend"
   ```
3. Run the admin creation script:
   ```bash
   python create_admin.py
   ```
4. Follow the prompts to enter admin details

## Troubleshooting

### Error: "Access denied for user 'root'@'localhost'"
- Make sure you're using the correct password
- Try resetting MySQL root password if forgotten

### Error: "Can't connect to MySQL server"
- Make sure MySQL service is running:
  - Windows: Check Services (services.msc) for "MySQL80"
  - Mac: `brew services start mysql`
  - Linux: `sudo systemctl start mysql`

### Error: "Unknown database 'job_workspace'"
- Make sure you created the database first (Step 3)
- Or the schema.sql file will create it automatically with `CREATE DATABASE IF NOT EXISTS`

### Error: "Table already exists"
- This is okay if you're re-running the script
- The `IF NOT EXISTS` clauses prevent errors
- If you want a fresh start, drop the database first:
  ```sql
  DROP DATABASE job_workspace;
  CREATE DATABASE job_workspace;
  ```

## Next Steps

After the database is set up:

1. **Configure Backend**: Update `backend/.env` file with your MySQL credentials:
   ```
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DATABASE=job_workspace
   ```

2. **Test Connection**: Run the backend to test the database connection:
   ```bash
   cd backend
   python run.py
   ```

3. **Create Admin User**: Run `python create_admin.py` to create your first admin account

## Quick Reference Commands

```sql
-- Connect to MySQL
mysql -u root -p

-- Create database
CREATE DATABASE job_workspace;

-- Use database
USE job_workspace;

-- Show all tables
SHOW TABLES;

-- View table structure
DESCRIBE users;

-- View all users
SELECT * FROM users;
```

