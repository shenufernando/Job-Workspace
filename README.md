# Job Workspace 🚀

An end-to-end, intelligent web platform engineered to seamlessly connect clients (Job Providers) with local professionals (Workers). The platform bridges real-world geographical constraints dynamically through advanced algorithms paired with deep-learning Natural Language Processing (BERT).

Experience secure job postings, instantaneous AI-powered matching, multimodal real-time messaging, and comprehensive WebRTC peer-to-peer audiovisual chat solutions inside a sleek, frictionless, and modern SaaS-style interface.

---

## ✨ Key Features

- **🤖 AI-Powered Job Matching**: Utilizes a fine-tuned Hugging Face **BERT** neural network (`BertForSequenceClassification`) to analyze job titles and descriptions against worker profiles, combined with geographic proximity scoring (`geopy`) for hyper-relevant recommendations.
- **🔐 Secure RBAC Authentication**: Role-Based Access Control dividing the platform into Admin, Provider, and Worker. Secures routes via stateless JSON Web Tokens (JWT) and mathematical `bcrypt` password hashing.
- **📍 Dynamic Geofencing & Topography**: Calculates exact integer radii and distances between users using OpenStreetMap (`Nominatim`) and geodesic algorithms, ensuring local jobs stay local.
- **💬 Real-Time Multimodal Chat**: Comprehensive text, image sharing, and in-browser native Audio Voice Notes (via `MediaRecorder` API).
- **📹 Native WebRTC A/V Calling**: Deep integration with Jitsi Meet for seamless, secure peer-to-peer video and audio calls directly within the application iframe.
- **🎨 Ultra-Premium "Card on Canvas" UI**: A fully custom, zero-dependency modern light-theme UI utilizing sophisticated glassmorphism, precise drop-shadows, CSS variables, and fluid animations.

---

## 🛠️ Technology Stack

### **Frontend (Presentation Tier)**
- **HTML5 / CSS3**: Custom "SaaS-style" design system (No external frameworks like Bootstrap or Tailwind used, demonstrating extreme CSS mastery).
- **Vanilla JavaScript**: DOM manipulation, asynchronous Fetch API integrations, WebRTC triggers, and `MediaRecorder` blob handling.
- **SweetAlert2 & FontAwesome**: For premium popups and scalable vector typography.

### **Backend (Application Tier)**
- **Python 3.x & Flask**: Lightweight, decoupled RESTful API architecture.
- **Flask-JWT-Extended**: For robust, stateless API endpoint security.
- **Machine Learning**: `PyTorch` and `Transformers` (Hugging Face) for parsing NLP data.
- **Geocoding**: `geopy` for backend geographic distance calculations.

### **Database (Data Tier)**
- **MySQL**: Relational SQL database managed via `mysql-connector-python`.

### **Testing & CI**
- **pytest**: Automated testing suite bridging API integration flows and granular ML inference validation.

---

## ⚙️ Prerequisites & Setup Instructions

### 1. Environment Requirements
- **Python 3.8+** installed.
- **MySQL Server** installed and running.

### 2. Database Initialization
1. Create a logical database in MySQL:
   ```sql
   CREATE DATABASE job_workspace;
   ```
2. The necessary tables (`users`, `job_posts`, `job_applications`, `messages`, `notifications`, `reviews`) will need to be imported or run via your setup script (see `DATABASE_SETUP.md` if applicable).

### 3. Backend Setup

1. **Navigate to the Backend**:
   ```bash
   cd backend
   ```
2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure the Environment (`.env`)**:
   Create a `.env` file in the `/backend` directory matching this configuration exactly:
   ```env
   SECRET_KEY=your-secret-key-change-in-production
   JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DATABASE=job_workspace
   DEBUG=True
   PORT=5000
   
   # For Background Registration Emails 
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   ```

### 4. Machine Learning Model Setup
The backend utilizes a heavily trained NLP model to predict roles. Ensure your pre-trained BERT weights are located in the following exact directory structure:
```
backend/
└── utils/
    └── bert_job_model/
        ├── config.json
        ├── model.safetensors (or pytorch_model.bin)
        ├── tokenizer_config.json
        └── vocab.txt
```
*(Note: If the `bert_job_model` folder is missing, the AI matching route (`/api/jobs/matches`) will fail gracefully or throw a 500 Server Error depending on `DEBUG` config).*

---

## 🚀 Running the Application

Because this uses a detached Frontend/Backend architecture, you must run two separate local servers.

### Terminal 1: Start the Backend (Flask API)
```bash
cd backend
python app.py
```
*The backend should default to `http://localhost:5000`.*

### Terminal 2: Start the Frontend (UI)
```bash
cd frontend
python -m http.server 8000
```
*The web interface is now accessible at `http://localhost:8000`.*

Open your web browser and navigate to **`http://localhost:8000`** to interact with the platform.

---

## 🧪 Running the Automated Tests

The application is bundled with a comprehensive PyTest suite mapped specifically to API authentication, Job algorithmic postings, and ML NLP Inference mapping.

To execute the tests:

1. Ensure the MySQL Database is active and the `.env` file is populated.
2. Navigate to the backend:
   ```bash
   cd backend
   ```
3. Run `pytest` pointing to the testing directory:
   ```bash
   pytest tests/ -v
   ```
   **OR** run the automated harness script:
   ```bash
   python run_tests.py
   ```

The output will validate tokens, CRUD operations, bounding boxes, and BERT inferential mathematics natively.
