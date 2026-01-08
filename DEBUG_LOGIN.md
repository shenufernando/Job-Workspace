# Debug Login Issues - Step by Step Guide

## Current Issue: Auto-logout after login

Follow these steps to identify the exact problem:

### Step 1: Clear Everything and Start Fresh

1. **Clear Browser Storage:**
   - Press F12 → Application tab
   - Click "Clear storage" → Check all boxes → "Clear site data"

2. **Restart Backend:**
   - Stop the backend server (Ctrl+C)
   - Start it again: `cd backend && python run.py`

### Step 2: Test Login with Console Open

1. **Open Browser Console (F12)**
2. **Go to Login Page**
3. **Before clicking Login, run this in console:**
   ```javascript
   console.log('=== LOGIN DEBUG START ===');
   ```

4. **Enter credentials and click Login**
5. **Watch the console for these messages:**
   - "Attempting login for: [email]"
   - "Sending login request..."
   - "Making request to: http://localhost:5000/api/login"
   - "Token being sent: [should show token]"
   - "Response status: [should be 200]"
   - "Login response received: [should show token and user]"
   - "Token saved: true"
   - "User saved: [user object]"

### Step 3: Check What Happens After Redirect

After login, when you're redirected to admin dashboard:

1. **Check Console for:**
   - "Admin dashboard - Checking auth..."
   - "Token exists: true"
   - "User exists: true"
   - "User role: admin"
   - "Authentication successful - loading dashboard"

2. **If you see "Authentication failed":**
   - Check what it says: "Token exists: false" or "User role: undefined"?

### Step 4: Check Network Tab

1. **Open Network tab in DevTools**
2. **Try to login**
3. **Look for `/api/login` request:**
   - Status should be 200
   - Response should have `token` and `user`

4. **After redirect, look for `/api/admin/dashboard` request:**
   - Status code?
   - If 401: Check Response tab for error message
   - Check Request Headers → Authorization header exists?

### Step 5: Manual Token Test

After logging in, before it redirects, run in console:

```javascript
// Check if token is saved
const token = localStorage.getItem('token');
const user = localStorage.getItem('user');
console.log('Token:', token);
console.log('User:', user);

// Test the token manually
fetch('http://localhost:5000/api/admin/dashboard', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(r => r.json())
.then(d => console.log('✅ Token works:', d))
.catch(e => console.error('❌ Token failed:', e));
```

### Step 6: Check Backend Logs

Look at the terminal where `python run.py` is running:

- When you login, do you see any errors?
- When dashboard loads, do you see "JWT verification error"?

## Common Issues and Fixes

### Issue 1: Token not being saved
**Symptoms:** Console shows "Token saved: false"
**Fix:** Check browser localStorage permissions

### Issue 2: Token invalid
**Symptoms:** 401 error with "Invalid token"
**Fix:** 
- Check JWT_SECRET_KEY in .env matches
- Restart backend after changing .env

### Issue 3: Token not sent
**Symptoms:** 401 error with "Authorization token is missing"
**Fix:** Check if Authorization header is in request

### Issue 4: Wrong role
**Symptoms:** Dashboard redirects even with valid token
**Fix:** Check user.role in localStorage matches 'admin'

## Quick Test Script

Copy and paste this in browser console after login:

```javascript
async function testAuth() {
  console.log('=== AUTH TEST ===');
  
  // Check localStorage
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  
  console.log('1. Token exists:', !!token);
  console.log('2. User exists:', !!user);
  console.log('3. User role:', user.role);
  console.log('4. Token length:', token?.length);
  
  if (!token) {
    console.error('❌ NO TOKEN IN STORAGE');
    return;
  }
  
  // Test token
  try {
    const response = await fetch('http://localhost:5000/api/admin/dashboard', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    console.log('5. API Response Status:', response.status);
    console.log('6. API Response Data:', data);
    
    if (response.status === 200) {
      console.log('✅ AUTHENTICATION WORKS!');
    } else {
      console.error('❌ AUTHENTICATION FAILED:', data);
    }
  } catch (e) {
    console.error('❌ REQUEST FAILED:', e);
  }
}

testAuth();
```

## What to Report

If still not working, please provide:

1. **Console output** (copy all messages from console)
2. **Network tab** (screenshot of `/api/admin/dashboard` request)
3. **Backend terminal output** (any error messages)
4. **Result of test script above**

