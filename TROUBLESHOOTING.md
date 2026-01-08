# Troubleshooting Guide - Login Issues

## Can't Login to Admin Dashboard

### Step 1: Verify Admin User Exists

1. **Check if admin user was created:**
   ```bash
   cd backend
   python create_admin.py
   ```
   - If you see "Email already exists!", the admin user exists
   - If it creates a new user, note the email and password you used

2. **Verify in MySQL:**
   - Open MySQL Workbench
   - Run this query:
   ```sql
   USE job_workspace;
   SELECT id, name, email, role FROM users WHERE role = 'admin';
   ```
   - You should see your admin user

### Step 2: Check Backend Server

1. **Make sure backend is running:**
   ```bash
   cd backend
   python run.py
   ```
   
2. **Verify server is accessible:**
   - Open browser and go to: `http://localhost:5000/api/health`
   - You should see: `{"status": "healthy"}`

3. **Check for errors in terminal:**
   - Look for any error messages in the terminal where the server is running
   - Common issues:
     - Database connection errors
     - Port already in use (change PORT in .env)

### Step 3: Check Database Connection

1. **Verify .env file exists:**
   - Location: `backend/.env`
   - Should contain:
   ```
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_actual_password
   MYSQL_DATABASE=job_workspace
   ```

2. **Test database connection:**
   - Try running `python create_admin.py` again
   - If it connects successfully, database is fine
   - If you get connection errors, check your MySQL password

### Step 4: Check Browser Console

1. **Open Developer Tools (F12)**
2. **Go to Console tab**
3. **Try to login and check for errors:**
   - Look for red error messages
   - Common errors:
     - `ERR_CONNECTION_REFUSED` - Backend not running
     - `401 Unauthorized` - Wrong credentials
     - `Failed to fetch` - CORS or connection issue

4. **Check Network tab:**
   - Go to Network tab in DevTools
   - Try to login
   - Click on the `/api/login` request
   - Check:
     - Status code (should be 200 for success)
     - Response body (should contain token and user data)
     - Request payload (check if credentials are sent)

### Step 5: Verify Credentials

1. **Make sure you're using the correct credentials:**
   - Email: The email you used when creating admin (e.g., `ravindunaveen123@gmail.com`)
   - Password: The password you set when creating admin

2. **Test with a simple query:**
   ```sql
   USE job_workspace;
   SELECT email, role FROM users WHERE role = 'admin';
   ```

### Step 6: Common Issues and Solutions

#### Issue: "Invalid credentials"
**Solution:**
- Double-check email and password
- Make sure password matches what you set in `create_admin.py`
- Try creating a new admin user again

#### Issue: "Cannot connect to server"
**Solution:**
- Make sure backend server is running (`python run.py`)
- Check if port 5000 is available
- Verify `http://localhost:5000/api/health` works

#### Issue: "Failed to fetch"
**Solution:**
- Backend server not running
- CORS issue (should be enabled, but check)
- Firewall blocking connection

#### Issue: Login succeeds but can't access dashboard
**Solution:**
- Check browser console for 401 errors
- Verify token is saved: Open DevTools → Application → Local Storage → Check for `token`
- Clear browser cache and try again

### Step 7: Reset and Try Again

If nothing works:

1. **Create a fresh admin user:**
   ```bash
   cd backend
   python create_admin.py
   ```
   - Use a simple email: `admin@test.com`
   - Use a simple password: `admin123`

2. **Clear browser data:**
   - Open DevTools (F12)
   - Application tab → Clear storage → Clear site data

3. **Try login again:**
   - Go to login page
   - Use the new credentials

### Step 8: Debug Mode

Add this to your browser console to debug:

```javascript
// Check if token exists
console.log('Token:', localStorage.getItem('token'));

// Check if user exists
console.log('User:', localStorage.getItem('user'));

// Test API connection
fetch('http://localhost:5000/api/health')
  .then(r => r.json())
  .then(d => console.log('API Health:', d))
  .catch(e => console.error('API Error:', e));
```

### Still Having Issues?

1. **Check backend logs:**
   - Look at the terminal where `python run.py` is running
   - Look for any error messages

2. **Verify all files are correct:**
   - `backend/.env` exists and has correct MySQL password
   - `backend/config.py` is loading .env correctly
   - Database `job_workspace` exists
   - All tables are created (run `database/schema.sql`)

3. **Test with curl or Postman:**
   ```bash
   curl -X POST http://localhost:5000/api/login \
     -H "Content-Type: application/json" \
     -d '{"username_or_email":"your_email","password":"your_password"}'
   ```

