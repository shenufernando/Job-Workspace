# Job Workspace - Multilingual Job Marketplace

A multilingual (Sinhala/English/Tamil) web platform connecting job providers with job seekers for informal jobs.

## Tech Stack
- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Flask)
- **Database**: MySQL

## Project Structure
```
Job Workspace/
├── backend/
│   ├── app.py
│   ├── run.py
│   ├── config.py
│   ├── create_admin.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── jobs.py
│   │   ├── payments.py
│   │   ├── reviews.py
│   │   ├── messages.py
│   │   ├── notifications.py
│   │   └── admin.py
│   ├── utils/
│   │   ├── database.py
│   │   ├── auth.py
│   │   └── ai_matching.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── main.js
│   │   └── i18n.js
│   └── pages/
│       ├── login.html
│       ├── signup.html
│       ├── worker-dashboard.html
│       ├── provider-dashboard.html
│       ├── admin-dashboard.html
│       ├── about.html
│       ├── services.html
│       └── contact.html
├── database/
│   └── schema.sql
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- MySQL Server (MySQL Workbench)
- Web browser

### 1. Database Setup
1. Open MySQL Workbench
2. Create a new database: `job_workspace`
3. Run the SQL script from `database/schema.sql`
4. Create an admin user by running:
   ```bash
   cd backend
   python create_admin.py
   ```

### 2. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file (copy from `.env.example` if available):
   ```
   SECRET_KEY=your-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-key-here
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=job_workspace
   DEBUG=True
   PORT=5000
   ```

4. Update the `.env` file with your MySQL credentials

5. Run the Flask application:
   ```bash
   python run.py
   ```
   
   Or alternatively:
   ```bash
   python app.py
   ```

   The API will be available at `http://localhost:5000`

### 3. Frontend Setup
1. Open `frontend/index.html` in a web browser
2. Or use a local server (recommended):
   ```bash
   # Using Python
   cd frontend
   python -m http.server 8000
   
   # Using Node.js (if you have it)
   npx http-server frontend -p 8000
   ```
3. Access the application at `http://localhost:8000`

### 4. Default Admin Account
After running `create_admin.py`, you can login with the admin credentials you created.

## Features
- ✅ Multilingual support (Sinhala/English/Tamil)
- ✅ User roles: Worker, Job Provider, Admin
- ✅ Job posting and application system
- ✅ AI-powered worker-job matching
- ✅ Payment and approval workflow
- ✅ Review and rating system
- ✅ Real-time messaging
- ✅ Notification system
- ✅ Profile management
- ✅ Worker recommendations
- ✅ Job recommendations

## API Endpoints

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login

### Jobs
- `GET /api/jobs` - Get all jobs (role-based filtering)
- `POST /api/jobs` - Create job (provider only)
- `GET /api/jobs/<id>` - Get job details
- `PUT /api/jobs/<id>` - Update job status (admin only)
- `POST /api/jobs/<id>/apply` - Apply for job (worker only)
- `GET /api/jobs/<id>/match` - Get matched workers (provider only)
- `GET /api/jobs/recommended` - Get recommended jobs (worker only)
- `PUT /api/jobs/<id>/complete` - Mark job as completed (provider only)

### Users
- `GET /api/profile` - Get current user profile
- `PUT /api/profile` - Update profile
- `GET /api/workers` - Get all workers
- `GET /api/users` - Get all users (admin only)
- `DELETE /api/users/<id>` - Delete user (admin only)

### Payments
- `POST /api/payments` - Create payment (provider only)
- `GET /api/payments` - Get payments

### Reviews
- `POST /api/reviews` - Create review (provider only)
- `GET /api/reviews/worker/<id>` - Get worker reviews
- `GET /api/reviews` - Get all reviews (admin only)
- `DELETE /api/reviews/<id>` - Delete review (admin only)

### Messages
- `POST /api/messages` - Send message
- `GET /api/messages/job/<id>` - Get messages for job
- `GET /api/messages/conversations` - Get all conversations

### Notifications
- `GET /api/notifications` - Get notifications
- `GET /api/notifications/unread` - Get unread count
- `PUT /api/notifications/<id>/read` - Mark as read
- `PUT /api/notifications/read-all` - Mark all as read

### Admin
- `GET /api/admin/dashboard` - Get dashboard statistics

## User Flow

1. **Registration**: Users sign up as Worker or Job Provider
2. **Login**: Users login and are redirected to their respective dashboards
3. **Job Posting** (Provider):
   - Provider creates a job post
   - Makes payment
   - Admin approves the job
   - AI suggests matching workers
   - Provider can invite workers or wait for applications
4. **Job Application** (Worker):
   - Worker views available jobs
   - Gets AI-powered recommendations
   - Applies for jobs
   - Provider accepts/rejects applications
5. **Communication**: Accepted workers and providers can message each other
6. **Completion**: Provider marks job as completed and reviews the worker

## Notes
- The AI matching algorithm uses location proximity, experience, and ratings
- Payment system is simplified (in production, integrate with payment gateways)
- Location coordinates are placeholders (in production, use geocoding API)
- Default admin user should be created using `create_admin.py`

## License
This project is created for educational purposes.
