from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy_serializer import SerializerMixin
import re

db = SQLAlchemy()

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")
        return email 

    @validates('name')
    def validate_name(self, key, name):
        if not name or len(name.strip()) == 0:
            raise ValueError("Name cannot be empty")
        return name      

    # Relationships
    graduates = db.relationship('Graduate', back_populates='user', uselist=False)
    admins = db.relationship('Admin', back_populates='user', uselist=False)
    admin_accesses = db.relationship('AdminAccess', back_populates='user')


class Graduate(db.Model, SerializerMixin):
    __tablename__ = 'graduate'

    graduate_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='graduates')
    job_applications = db.relationship('JobApplication', back_populates='graduate')
    payments = db.relationship('Payment', back_populates='graduate')
    normal_accesses = db.relationship('NormalAccess', back_populates='graduate')


class Admin(db.Model, SerializerMixin):
    __tablename__ = 'admin'

    admin_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='admins')
    admin_accesses = db.relationship('AdminAccess', back_populates='admin')


class Job(db.Model, SerializerMixin):
    __tablename__ = 'jobs'

    job_id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(255), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    requirements = db.Column(db.Text, nullable=False)
    salary = db.Column(db.Numeric(10, 2), nullable=False)
    posted_date = db.Column(db.TIMESTAMP, nullable=False)
    expiration_date = db.Column(db.TIMESTAMP, nullable=False)
    
    @validates('salary')
    def validate_salary(self, key, salary):
        if salary < 0:
            raise ValueError("Salary cannot be negative")
        return salary

    @validates('posted_date')
    def validate_posted_date(self, key, posted_date):
        if not posted_date:
            raise ValueError("Posted date cannot be null")
        return posted_date

    @validates('expiration_date')
    def validate_expiration_date(self, key, expiration_date):
        if not expiration_date:
            raise ValueError("Expiration date cannot be null")
        return expiration_date

    # Relationships
    job_applications = db.relationship('JobApplication', back_populates='job')
    normal_accesses = db.relationship('NormalAccess', back_populates='job')
    premium_accesses = db.relationship('PremiumAccess', back_populates='job')
    admin_accesses = db.relationship('AdminAccess', back_populates='job')


class JobApplication(db.Model, SerializerMixin):
    __tablename__ = 'job_applications'

    application_id = db.Column(db.Integer, primary_key=True)
    graduate_id = db.Column(db.Integer, db.ForeignKey('graduate.graduate_id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.job_id'), nullable=False)
    curriculum_vitae = db.Column(db.String(255), nullable=False)  # Store file path

    # Relationships
    graduate = db.relationship('Graduate', back_populates='job_applications')
    job = db.relationship('Job', back_populates='job_applications')


class Payment(db.Model, SerializerMixin):
    __tablename__ = 'payments'

    payment_id = db.Column(db.Integer, primary_key=True)
    graduate_id = db.Column(db.Integer, db.ForeignKey('graduate.graduate_id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())
    payment_method = db.Column(db.String(50), nullable=False)
    
    
    @validates('amount')
    def validate_amount(self, key, amount):
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        return amount

    @validates('payment_method')
    def validate_payment_method(self, key, payment_method):
        if not payment_method or len(payment_method.strip()) == 0:
            raise ValueError("Payment method cannot be empty")
        return payment_method


    # Relationships
    graduate = db.relationship('Graduate', back_populates='payments')
    premium_accesses = db.relationship('PremiumAccess', back_populates='payment')
    admin_accesses = db.relationship('AdminAccess', back_populates='payment')


class NormalAccess(db.Model, SerializerMixin):
    __tablename__ = 'normal_access'

    normal_id = db.Column(db.Integer, primary_key=True)
    graduate_id = db.Column(db.Integer, db.ForeignKey('graduate.graduate_id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.job_id'), nullable=False)

    # Relationships
    graduate = db.relationship('Graduate', back_populates='normal_accesses')
    job = db.relationship('Job', back_populates='normal_accesses')


class ExtraResource(db.Model, SerializerMixin):
    __tablename__ = 'extra_resources'

    resource_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    content_url = db.Column(db.String(255), nullable=False)

    @validates('title')
    def validate_title(self, key, title):
        if not title or len(title.strip()) == 0:
            raise ValueError("Title cannot be empty")
        return title
    
    @validates('content_url')
    def validate_content_url(self, key, content_url):     
        if not content_url or len(content_url.strip()) == 0:
            raise ValueError("Content URL cannot be empty")
        return content_url
    
    @validates('description')
    def validate_description(self, key, description):
        if not description or len(description.strip()) == 0:
            raise ValueError("Description cannot be empty")
        return description
    


    # Relationships
    premium_accesses = db.relationship('PremiumAccess', back_populates='resource')
    admin_accesses = db.relationship('AdminAccess', back_populates='resource')


class PremiumAccess(db.Model, SerializerMixin):
    __tablename__ = 'premium_access'

    premium_id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.payment_id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.job_id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('extra_resources.resource_id'), nullable=False)

    # Relationships
    payment = db.relationship('Payment', back_populates='premium_accesses')
    job = db.relationship('Job', back_populates='premium_accesses')
    resource = db.relationship('ExtraResource', back_populates='premium_accesses')


class AdminAccess(db.Model, SerializerMixin):
    __tablename__ = 'admin_access'

    access_id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.admin_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.job_id'), nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.payment_id'), nullable=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('extra_resources.resource_id'), nullable=True)

    # Relationships
    admin = db.relationship('Admin', back_populates='admin_accesses')
    user = db.relationship('User', back_populates='admin_accesses')
    job = db.relationship('Job', back_populates='admin_accesses')
    payment = db.relationship('Payment', back_populates='admin_accesses')
    resource = db.relationship('ExtraResource', back_populates='admin_accesses')
