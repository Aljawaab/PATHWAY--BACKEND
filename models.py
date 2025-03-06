from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy_serializer import SerializerMixin
import re
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False, default='normal')  # Roles: normal, premium, admin
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")
        return email
    
    @validates('role')
    def validate_role(self, key, role):
        if role not in ['normal', 'premium', 'admin']:
            raise ValueError("Invalid role")
        return role
    
    @validates('password_hash')
    def validate_password_hash(self, key, password_hash):
        if len(password_hash) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return password_hash
    
    def to_dict(self):
        user_dict = {
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "date_joined": self.date_joined,
            "payments": [payment.to_dict() for payment in self.payments],
            "applications": [app.to_dict() for app in self.applications]
        }
        return user_dict

    # Relationships
    payments = db.relationship('Payment', back_populates='user', cascade="all, delete")
    job_applications = db.relationship('JobApplication', back_populates='user', cascade="all, delete")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Job model
class Job(db.Model, SerializerMixin):
    __tablename__ = 'jobs'
    job_id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(255), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    requirements = db.Column(db.Text, nullable=False)
    salary = db.Column(db.Numeric(10, 2), nullable=False)
    posted_date = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())
    expiration_date = db.Column(db.TIMESTAMP, nullable=False)

    @validates('salary')
    def validate_salary(self, key, salary):
        if salary <= 0:
            raise ValueError("Salary must be greater than 0")
        return salary
    @validates('expiration_date')
    def validate_expiration_date(self, key, expiration_date):
        if expiration_date <= self.posted_date:
            raise ValueError("Expiration date must be after posted date")
        return expiration_date
    @validates('posted_date')
    def validate_posted_date(self, key, posted_date):
        if posted_date > db.func.current_timestamp():
            raise ValueError("Posted date must be in the past")
        return posted_date
    # Relationships
    job_applications = db.relationship('JobApplication', back_populates='job', cascade="all, delete")
    
    def to_dict(self):
        job_dict = {
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "job_type": self.job_type,
            "skills_required": self.skills_required,
            "benefits": self.benefits,
            "application_deadline": self.application_deadline,
            "employer": self.employer,
            "employer_email": self.employer_email,
            "employer_phone": self.employer_phone,
            "date_posted": self.date_posted,
            "is_active": self.is_active,
            "applications": [application.to_dict() for application in self.applications],
            "extra_resources": [resource.to_dict() for resource in self.extra_resources]
        }
        return job_dict

# JobApplication model
class JobApplication(db.Model, SerializerMixin):
    __tablename__ = 'job_applications'
    application_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.job_id'), nullable=False)
    #curriculum_vitae = db.Column(db.String(255), nullable=False)  # Store file path

    user = db.relationship('User', back_populates='job_applications')
    job = db.relationship('Job', back_populates='job_applications')
    
    def to_dict(self):
        app_dict = {
            "application_date": self.application_date,
            "status": self.status,
            "user": {
                "username": self.user.username,
                "email": self.user.email,
                "phone": self.user.phone,
                "role": self.user.role,
                "date_joined": self.user.date_joined
            },
            "job": {
                "title": self.job.title,
                "description": self.job.description,
                "location": self.job.location,
                "salary_min": self.job.salary_min,
                "salary_max": self.job.salary_max,
                "job_type": self.job.job_type,
                "skills_required": self.job.skills_required,
                "benefits": self.job.benefits,
                "application_deadline": self.job.application_deadline,
                "employer": self.job.employer,
                "employer_email": self.job.employer_email,
                "employer_phone": self.job.employer_phone,
                "date_posted": self.job.date_posted,
                "is_active": self.job.is_active
            }
        }
        return app_dict
# Payment model
class Payment(db.Model, SerializerMixin):
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())
    payment_method = db.Column(db.String(50), nullable=False)
    @validates('amount')
    def validate_amount(self, key, amount):
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        return amount
    @validates('payment_method')
    def validate_payment_method(self, key, payment_method):
        if payment_method not in ['credit_card', 'paypal']:
            raise ValueError("Invalid payment method")
        return payment_method
    
    # Relationships
    user = db.relationship('User', back_populates='payments')
    
    def to_dict(self):
        payment_dict = {
            "amount": self.amount,
            "payment_date": self.payment_date,
            "payment_status": self.payment_status,
            "user": {
                "username": self.user.username,
                "email": self.user.email,
                "phone": self.user.phone,
                "role": self.user.role,
                "date_joined": self.user.date_joined
            }
        }
        return payment_dict
    
# ExtraResource model
class ExtraResource(db.Model, SerializerMixin):
    __tablename__ = 'extra_resources'
    resource_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    #content_url = db.Column(db.String(255), nullable=False)
    @validates('title')
    def validate_title(self, key, title):
        if len(title) < 5:
            raise ValueError("Title must be at least 5 characters long")
        return title
    
    def to_dict(self):
        resource_dict = {
            "resource_name": self.resource_name,
            "description": self.description,
            "resource_type": self.resource_type,
            "job": {
                "title": self.job.title,
                "description": self.job.description,
                "location": self.job.location,
                "salary_min": self.job.salary_min,
                "salary_max": self.job.salary_max,
                "job_type": self.job.job_type,
                "skills_required": self.job.skills_required,
                "benefits": self.job.benefits,
                "application_deadline": self.job.application_deadline,
                "employer": self.job.employer,
                "employer_email": self.job.employer_email,
                "employer_phone": self.job.employer_phone,
                "date_posted": self.job.date_posted,
                "is_active": self.job.is_active
            }
        }
        return resource_dict
    