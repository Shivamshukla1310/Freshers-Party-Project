# Complete Fresher's Party Website with Flask
# Project Structure and All Files

"""
Project Structure:
freshers_party/
├── app.py
├── config.py
├── models.py
├── requirements.txt
├── run.py
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/
│       └── (your event images)
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── success.html
│   ├── admin/
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   └── scan_qr.html
│   └── emails/
│       └── qr_email.html
└── instance/
    └── freshers.db (will be created automatically)
"""

# ==================== app.py ====================
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import qrcode
import io
import base64
import uuid
import os
import csv
import razorpay
from PIL import Image

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'ajh@^#!#sd87632jhks&#%@da8723jgeknwm%!@$!@khasd823'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///freshers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tukaaramgore@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'gcio ynte oyap tqwv'     # Replace with your app password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

# Razorpay configuration (Test mode)
app.config['RAZORPAY_KEY_ID'] = 'rzp_test_your_key_id'
app.config['RAZORPAY_KEY_SECRET'] = 'your_key_secret'

db = SQLAlchemy(app)
mail = Mail(app)

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    qr_code = db.Column(db.String(200), unique=True, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    used_status = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_id = db.Column(db.String(100))
    order_id = db.Column(db.String(100))

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Event configuration
EVENT_CONFIG = {
    'name': 'Fresher\'s Party 2024',
    'date': '2024-12-15',
    'time': '6:00 PM',
    'venue': 'University Auditorium',
    'dress_code': 'Semi-Formal',
    'contact': '+91 9876543210',
    'whatsapp': '919876543210',
    'ticket_price': 500,  # In rupees
    'email': 'events@university.edu'
}

# Routes
@app.route('/')
def index():
    return render_template('index.html', event=EVENT_CONFIG)

@app.route('/register')
def register():
    return render_template('register.html', event=EVENT_CONFIG)

@app.route('/create_order', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        
        # Create Razorpay order
        order_data = {
            'amount': EVENT_CONFIG['ticket_price'] * 100,  # Amount in paisa
            'currency': 'INR',
            'receipt': f"receipt_{uuid.uuid4().hex[:10]}",
            'payment_capture': 1
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        return jsonify({
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key': app.config['RAZORPAY_KEY_ID']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/payment_success', methods=['POST'])
def payment_success():
    try:
        # Get payment details
        payment_data = request.get_json()
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': payment_data['razorpay_order_id'],
            'razorpay_payment_id': payment_data['razorpay_payment_id'],
            'razorpay_signature': payment_data['razorpay_signature']
        }
        
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except:
            return jsonify({'success': False, 'error': 'Payment verification failed'})
        
        # Generate unique QR code
        qr_code = str(uuid.uuid4())
        
        # Create user record
        user = User(
            name=payment_data['name'],
            email=payment_data['email'],
            mobile=payment_data['mobile'],
            qr_code=qr_code,
            payment_status='completed',
            payment_id=payment_data['razorpay_payment_id'],
            order_id=payment_data['razorpay_order_id']
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Generate QR code image
        qr_img = generate_qr_code(qr_code)
        
        # Send email with QR code
        send_qr_email(user.email, user.name, qr_img, qr_code)
        
        return jsonify({
            'success': True,
            'message': 'Payment successful! QR code sent to your email.',
            'qr_code': qr_code
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/success')
def success():
    return render_template('success.html', event=EVENT_CONFIG)

# Admin routes
@app.route('/admin')
def admin_login():
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    username = request.form['username']
    password = request.form['password']
    
    admin = Admin.query.filter_by(username=username).first()
    
    if admin and check_password_hash(admin.password_hash, password):
        session['admin_logged_in'] = True
        session['admin_username'] = username
        return redirect(url_for('admin_dashboard'))
    
    flash('Invalid credentials')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    total_registrations = User.query.count()
    total_payments = User.query.filter_by(payment_status='completed').count()
    total_entries = User.query.filter_by(used_status=True).count()
    total_revenue = total_payments * EVENT_CONFIG['ticket_price']
    
    users = User.query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/dashboard.html', 
                         total_registrations=total_registrations,
                         total_payments=total_payments,
                         total_entries=total_entries,
                         total_revenue=total_revenue,
                         users=users,
                         event=EVENT_CONFIG)

@app.route('/admin/scan_qr')
def admin_scan_qr():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin/scan_qr.html')

@app.route('/admin/validate_qr', methods=['POST'])
def validate_qr():
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    qr_code = request.json.get('qr_code')
    
    user = User.query.filter_by(qr_code=qr_code).first()
    
    if not user:
        return jsonify({'success': False, 'error': 'Invalid QR code'})
    
    if user.payment_status != 'completed':
        return jsonify({'success': False, 'error': 'Payment not completed'})
    
    if user.used_status:
        return jsonify({'success': False, 'error': 'QR code already used', 'user': user.name})
    
    # Mark as used
    user.used_status = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Entry granted for {user.name}',
        'user': {
            'name': user.name,
            'email': user.email,
            'mobile': user.mobile
        }
    })

@app.route('/admin/export_csv')
def export_csv():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Name', 'Email', 'Mobile', 'Payment Status', 'Entry Status', 'Registration Date'])
    
    # Write data
    users = User.query.all()
    for user in users:
        writer.writerow([
            user.id,
            user.name,
            user.email,
            user.mobile,
            user.payment_status,
            'Used' if user.used_status else 'Not Used',
            user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'freshers_party_registrations_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))

# Utility functions
def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for email
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return base64.b64encode(img_buffer.getvalue()).decode()

def send_qr_email(email, name, qr_img_base64, qr_code):
    try:
        msg = Message(
            subject=f'Your {EVENT_CONFIG["name"]} Entry Pass',
            recipients=[email],
            html=render_template('emails/qr_email.html', 
                               name=name, 
                               event=EVENT_CONFIG,
                               qr_code=qr_code)
        )
        
        # Attach QR code image
        qr_img_data = base64.b64decode(qr_img_base64)
        msg.attach(f"{qr_code}.png", "image/png", qr_img_data)
        
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

# Initialize database and create admin user
# @app.before_first_request
# def create_tables():
#     db.create_all()

with app.app_context():
    db.create_all()
    
    # Create default admin if not exists
    admin = Admin.query.filter_by(username='admin').first()
    if not admin:
        admin = Admin(
            username='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default admin if not exists
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=True)

# ==================== requirements.txt ====================
"""
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Mail==0.9.1
Werkzeug==2.3.7
qrcode[pil]==7.4.2
razorpay==1.4.1
Pillow==10.0.1
"""

# ==================== run.py ====================
"""
from app import app, db

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
"""
