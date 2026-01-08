from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import Config
from routes.auth import auth_bp
from routes.users import users_bp
from routes.jobs import jobs_bp
from routes.payments import payments_bp
from routes.reviews import reviews_bp
from routes.messages import messages_bp
from routes.notifications import notifications_bp
from routes.admin import admin_bp

app = Flask(__name__)
app.config.from_object(Config)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = Config.JWT_ACCESS_TOKEN_EXPIRES

# Enable CORS
CORS(app, origins="*", supports_credentials=True)

# Initialize JWT
jwt = JWTManager(app)

# JWT Error Handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization token is missing'}), 401

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(users_bp, url_prefix='/api')
app.register_blueprint(jobs_bp, url_prefix='/api')
app.register_blueprint(payments_bp, url_prefix='/api')
app.register_blueprint(reviews_bp, url_prefix='/api')
app.register_blueprint(messages_bp, url_prefix='/api')
app.register_blueprint(notifications_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api')

# Register database teardown
from utils.database import close_db
app.teardown_appcontext(close_db)

@app.route('/')
def index():
    return {'message': 'Job Workspace API', 'status': 'running'}

@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, port=Config.PORT, host='0.0.0.0')
