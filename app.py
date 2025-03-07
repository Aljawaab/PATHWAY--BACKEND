from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_cors import CORS
from models import db, User, Job, JobApplication, Payment, ExtraResource
import datetime
from flask import Response
import bcrypt

app = Flask(__name__)
cors = CORS(app, origins="*")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Job.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change to a secure key

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

class BaseRoute(Resource):
    def get(self):
        return jsonify({
            "message": "Welcome to the Job Management API! Below are the available routes:",
            "routes": {
                "/get_jobs": "Retrieve all jobs.",
                "/get_job": "Retrieve a job by ID or job name (e.g., /get_job?job_id=1 or /get_job?job_name=Software Engineer).",
                "/get_users": "Retrieve all users.",
                "/get_user": "Retrieve a user by ID or username (e.g., /get_user?user_id=1 or /get_user?username=john_doe).",
                "/add_user": "Add a new user.",
                "/update_user/<int:user_id>": "Update a user by ID.",
                "/delete_user/<int:user_id>": "Delete a user by ID.",
                "/get_payments": "Retrieve all payments.",
                "/get_payment": "Retrieve a payment by ID or username (e.g., /get_payment?payment_id=1 or /get_payment?username=john_doe).",
                "/add_payment": "Add a new payment.",
                "/get_job_resources": "Retrieve all extra resources for a job.",
                "/get_job_resource": "Retrieve a resource by ID, job name, or resource type (e.g., /get_job_resource?resource_id=1 or /get_job_resource?job_name=Software Engineer or /get_job_resource?resource_type=Document).",
                "/add_job_resource": "Add a new extra resource.",
                "/update_job_resource/<int:resource_id>": "Update a resource by ID.",
                "/delete_job_resource/<int:resource_id>": "Delete a resource by ID.",
                "/get_applications": "Retrieve all job applications.",
                "/get_application": "Retrieve a job application by ID, username, or job name (e.g., /get_application?application_id=1 or /get_application?username=john_doe or /get_application?job_name=Software Engineer).",
                "/add_application": "Add a new job application.",
            }
        })
# Job Routes
class GetJobs(Resource):
    def get(self):
        jobs = Job.query.all()  # Retrieve all jobs
        jobs_list = []
        for job in jobs:
            job_data = job.to_dict()  # Get the full job dict
            job_data.pop('applications', None)  # Remove applications field if present
            job_data.pop('extra_resources', None)  # Remove extra_resources field if present
            jobs_list.append(job_data)
        return jsonify(jobs_list)  # Return the filtered list of jobs


class GetJob(Resource):
    def get(self):
        job_id = request.args.get('job_id', type=int)
        job_name = request.args.get('job_name', type=str)

        if job_id:
            job = Job.query.get(job_id)
            if not job:
                # Return error as plain text
                return Response(f"Job with ID {job_id} not found.", status=404, mimetype='text/plain')
        elif job_name:
            job = Job.query.filter_by(title=job_name).first()
            if not job:
                # Return error as plain text
                return Response(f"Job with name '{job_name}' not found.", status=404, mimetype='text/plain')
        else:
            # Return error as plain text
            return Response("Either 'job_id' or 'job_name' must be provided.", status=400, mimetype='text/plain')

        # If the job is found, remove unwanted fields and return job data as JSON
        job_data = job.to_dict()  # Get the full job dict
        job_data.pop('applications', None)  # Remove applications field
        job_data.pop('extra_resources', None)  # Remove extra_resources field
        return jsonify(job_data)  # Return the filtered job dat

    

# User Routes
class GetUsers(Resource):
    def get(self):
        users = User.query.all()
        users_list = []
        for user in users:
            user_data = user.to_dict()
            user_data.pop('applications', None)
            user_data.pop('payments', None)
            users_list.append(user_data)
        return jsonify(users_list)

class GetUser(Resource):
    def get(self):
        user_id = request.args.get('user_id', type=int)
        username = request.args.get('username', type=str)

        if user_id:
            user = User.query.get(user_id)
            if not user:
                # Return error as plain text
                return Response(f"User with ID {user_id} not found.", status=404, mimetype='text/plain')
        elif username:
            user = User.query.filter_by(username=username).first()
            if not user:
                # Return error as plain text
                return Response(f"User with username '{username}' not found.", status=404, mimetype='text/plain')
        else:
            # Return error as plain text
            return Response("Either 'user_id' or 'username' must be provided.", status=400, mimetype='text/plain')

        # If the user is found, remove unwanted fields and return user data as JSON
        user_data = user.to_dict()
        user_data.pop('applications', None)
        user_data.pop('payments', None)
        return jsonify(user_data)  # Return the filtered user data as JSON
    
    
class AddUser(Resource):
    def post(self):
        data = request.get_json()

        try:
            # Ensure username, email, and password are provided
            if not data.get('username') or not data.get('email') or not data.get('password'):
                return jsonify({"error": "Username, email, and password are required."}), 400

            # Extract the email
            email = data['email']

            # Determine the user's role based on the email structure
            if email.endswith('.admin@gmail.com') or '.admin' in email.split('@')[-1]:
                role = 'admin'
            else:
                role = 'graduate'

            # Hash the password before storing it
            password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

            # Create the user object
            user = User(
                username=data['username'],
                email=email,
                phone=data.get('phone'),  # Optional
                password_hash=password_hash,
                role=role  # Set the role based on the email structure
            )

            # Add the user to the database
            db.session.add(user)
            db.session.commit()

            # Respond with the created user (excluding password hash)
            return jsonify({
                'message': 'User created successfully!',
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'role': user.role
            }), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 400


class UpdateUser(Resource):
    def put(self, user_id):
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        try:
            user.username = data.get('username', user.username)
            user.email = data.get('email', user.email)
            user.phone = data.get('phone', user.phone)
            user.password_hash = data.get('password_hash', user.password_hash)
            user.role = data.get('role', user.role)

            # Update related applications
            applications = JobApplication.query.filter_by(user_id=user.id).all()
            for app in applications:
                app.user.username = user.username
                app.user.email = user.email
                app.user.phone = user.phone
                db.session.commit()

            # Update related payments
            payments = Payment.query.filter_by(user_id=user.id).all()
            for payment in payments:
                payment.user.username = user.username
                payment.user.email = user.email
                payment.user.phone = user.phone
                db.session.commit()

            db.session.commit()
            return jsonify(user.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 400

class DeleteUser(Resource):
    def delete(self, user_id):
        user = User.query.get_or_404(user_id)

        # Keep job applications and payments but retain user data in them
        applications = JobApplication.query.filter_by(user_id=user.id).all()
        for app in applications:
            app.username = user.username
            app.email = user.email
            app.phone = user.phone
            db.session.commit()

        payments = Payment.query.filter_by(user_id=user.id).all()
        for payment in payments:
            payment.username = user.username
            payment.email = user.email
            payment.phone = user.phone
            db.session.commit()

        # Delete the user, but retain the user info in applications and payments
        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "User deleted but related applications and payments retained."})

# Payment Routes
class GetPayments(Resource):
    def get(self):
        payments = Payment.query.all()
        return jsonify([payment.to_dict() for payment in payments])

class GetPayment(Resource):
    def get(self):
        payment_id = request.args.get('payment_id', type=int)
        username = request.args.get('username', type=str)

        # Check for payment_id
        if payment_id:
            payment = Payment.query.get(payment_id)  # .get() is used for getting by ID
            if payment:
                return jsonify(payment.to_dict())
            else:
                # Return error as plain text
                return Response("Payment not found with the provided ID.", status=404, mimetype='text/plain')

        # Check for username
        elif username:
            user = User.query.filter_by(username=username).first()
            if user:
                payments = Payment.query.filter_by(user_id=user.id).all()
                if payments:
                    return jsonify([payment.to_dict() for payment in payments])
                else:
                    # Return error as plain text
                    return Response("No payments found for the provided username.", status=404, mimetype='text/plain')
            else:
                # Return error as plain text
                return Response("User with the provided username does not exist.", status=404, mimetype='text/plain')

        # If neither payment_id nor username is provided
        else:
            # Return error as plain text
            return Response("Either 'payment_id' or 'username' must be provided.", status=400, mimetype='text/plain')


class AddPayment(Resource):
    def post(self):
        data = request.get_json()
        try:
            payment = Payment(
                user_id=data['user_id'],
                amount=5000.0,
                payment_status=data.get('payment_status', 'completed'),
                payment_date=datetime.datetime.strptime(data['payment_date'], '%Y-%m-%d %H:%M:%S')
            )
            db.session.add(payment)
            db.session.commit()

            user = User.query.get(data['user_id'])
            if payment.amount == 5000 and payment.payment_status == 'completed':
                user.role = 'premium'
                db.session.commit()

            return jsonify(payment.to_dict()), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# Extra Resource Routes
class GetResources(Resource):
    def get(self):
        resources = ExtraResource.query.all()
        return jsonify([resource.to_dict() for resource in resources])


class GetResource(Resource):
    def get(self):
        resource_id = request.args.get('resource_id', type=int)
        job_name = request.args.get('job_name', type=str)
        resource_type = request.args.get('resource_type', type=str)

        # Handle resource_id
        if resource_id:
            resource = ExtraResource.query.get(resource_id)
            if resource:
                return jsonify(resource.to_dict())  # No iteration needed for a single object
            else:
                # Return error as plain text
                return Response("Resource not found with the provided ID.", status=404, mimetype='text/plain')

        # Handle job_name
        elif job_name:
            job = Job.query.filter_by(title=job_name).first()
            if job:
                resources = ExtraResource.query.filter_by(job_id=job.id).all()
                if resources:
                    return jsonify([resource.to_dict() for resource in resources])
                else:
                    # Return error as plain text
                    return Response("No resources found for this job.", status=404, mimetype='text/plain')

        # Handle resource_type
        elif resource_type:
            resources = ExtraResource.query.filter_by(resource_type=resource_type).all()
            if resources:
                return jsonify([resource.to_dict() for resource in resources])
            else:
                # Return error as plain text
                return Response("No resources found for this type.", status=404, mimetype='text/plain')

        # If neither resource_id, job_name, nor resource_type is provided
        else:
            # Return error as plain text
            return Response("Provide either 'resource_id', 'job_name', or 'resource_type'.", status=400, mimetype='text/plain')


class AddResource(Resource):
    def post(self):
        data = request.get_json()

        if not data.get('job_id') or not data.get('resource_name') or not data.get('resource_type'):
            return jsonify({"error": "job_id, resource_name, and resource_type are required fields."}), 400

        try:
            job = Job.query.get(data['job_id'])
            if not job:
                job = Job(
                    title=data['job_title'],
                    location=data['job_location'],
                    salary_min=data['salary_min'],
                    salary_max=data['salary_max'],
                    job_type=data['job_type'],
                    skills_required=data['skills_required'],
                    benefits=data['benefits'],
                    application_deadline=data['application_deadline'],
                    employer=data['employer'],
                    employer_email=data['employer_email'],
                    employer_phone=data['employer_phone']
                )
                db.session.add(job)
                db.session.commit()

            resource = ExtraResource(
                job_id=job.id,
                resource_name=data['resource_name'],
                description=data.get('description', ''),
                resource_type=data['resource_type']
            )
            db.session.add(resource)
            db.session.commit()

            return jsonify(resource.to_dict()), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

class UpdateResource(Resource):
    def put(self, resource_id):
        resource = ExtraResource.query.get_or_404(resource_id)
        data = request.get_json()

        try:
            resource.job_id = data.get('job_id', resource.job_id)
            resource.resource_name = data.get('resource_name', resource.resource_name)
            resource.description = data.get('description', resource.description)
            resource.resource_type = data.get('resource_type', resource.resource_type)

            if 'job_id' in data:
                job = Job.query.get(data['job_id'])
                if job:
                    job.title = data.get('job_title', job.title)
                    job.location = data.get('job_location', job.location)
                    job.salary_min = data.get('salary_min', job.salary_min)
                    job.salary_max = data.get('salary_max', job.salary_max)
                    job.job_type = data.get('job_type', job.job_type)
                    job.skills_required = data.get('skills_required', job.skills_required)
                    job.benefits = data.get('benefits', job.benefits)
                    job.application_deadline = data.get('application_deadline', job.application_deadline)
                    job.employer = data.get('employer', job.employer)
                    job.employer_email = data.get('employer_email', job.employer_email)
                    job.employer_phone = data.get('employer_phone', job.employer_phone)

                    db.session.commit()

                    applications = JobApplication.query.filter_by(job_id=job.id).all()
                    for app in applications:
                        app.job.title = job.title
                        app.job.location = job.location
                        app.job.salary_min = job.salary_min
                        app.job.salary_max = job.salary_max
                        app.job.job_type = job.job_type
                        app.job.skills_required = job.skills_required
                        app.job.benefits = job.benefits
                        app.job.application_deadline = job.application_deadline
                        db.session.commit()

            db.session.commit()
            return jsonify(resource.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 400

class DeleteResource(Resource):
    def delete(self, resource_id):
        resource = ExtraResource.query.get_or_404(resource_id)
        job = Job.query.get_or_404(resource.job_id)

        # Get all related applications and retain job info in them
        related_applications = JobApplication.query.filter_by(job_id=job.id).all()
        for app in related_applications:
            # Keep the job details in the application, even if job is deleted
            app.job_title = job.title
            app.job_location = job.location
            app.salary_min = job.salary_min
            app.salary_max = job.salary_max
            app.job_type = job.job_type
            app.skills_required = job.skills_required
            app.benefits = job.benefits
            app.application_deadline = job.application_deadline

            db.session.commit()

        # Check if the job still has other resources; if not, delete the job
        remaining_resources = ExtraResource.query.filter_by(job_id=job.id).all()
        if not remaining_resources:
            db.session.delete(job)
        
        # Delete the resource (but not the job data from applications)
        db.session.delete(resource)
        db.session.commit()

        return jsonify({"message": "Resource deleted, but job information retained in applications."})        

# Job Application Routes
class GetApplications(Resource):
    def get(self):
        applications = JobApplication.query.all()
        return jsonify([application.to_dict() for application in applications])


class GetApplication(Resource):
    def get(self):
        try:
            application_id = request.args.get('application_id', type=int)
            username = request.args.get('username', type=str)
            job_name = request.args.get('job_name', type=str)

            # Handle application_id search
            if application_id:
                application = JobApplication.query.get(application_id)
                if application:
                    return jsonify(application.to_dict())  # Return application as JSON
                else:
                    return Response(f"Application not found with ID {application_id}.", status=404, mimetype='text/plain')

            # Handle username search
            elif username:
                user = User.query.filter_by(username=username).first()
                if user:
                    applications = JobApplication.query.filter_by(user_id=user.id).all()
                    if applications:
                        return jsonify([application.to_dict() for application in applications])
                    else:
                        return Response(f"No applications found for user '{username}'.", status=404, mimetype='text/plain')
                else:
                    return Response(f"User with username '{username}' does not exist.", status=404, mimetype='text/plain')

            # Handle job_name search
            elif job_name:
                job = Job.query.filter_by(title=job_name).first()
                if job:
                    applications = JobApplication.query.filter_by(job_id=job.id).all()
                    if applications:
                        return jsonify([application.to_dict() for application in applications])
                    else:
                        return Response(f"No applications found for job '{job_name}'.", status=404, mimetype='text/plain')

            # If none of the parameters are provided
            else:
                return Response("Please provide either 'application_id', 'username', or 'job_name'.", status=400, mimetype='text/plain')

        except Exception as e:
            # Return a plain text error message
            return Response(f"An error occurred: {str(e)}", status=500, mimetype='text/plain')




                       
class AddApplication(Resource):
    def post(self):
        data = request.get_json()

        try:
            application = JobApplication(
                user_id=data['user_id'],
                job_id=data['job_id'],
                status=data.get('status', 'pending'),
                cover_letter=data.get('cover_letter', ''),
                date_applied=datetime.datetime.strptime(data['date_applied'], '%Y-%m-%d %H:%M:%S')
            )
            db.session.add(application)
            db.session.commit()

            return jsonify(application.to_dict()), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# Add resources to API with specific HTTP methods and unique routes
api.add_resource(BaseRoute, '/')
api.add_resource(GetJobs, '/get_jobs')
api.add_resource(GetJob, '/get_job')  # Changed this route to handle both job ID and job name
api.add_resource(GetUsers, '/get_users')
api.add_resource(GetUser, '/get_user')  # Changed this route to handle both user ID and username
api.add_resource(AddUser, '/add_user')
api.add_resource(UpdateUser, '/update_user/<int:user_id>')
api.add_resource(DeleteUser, '/delete_user/<int:user_id>')

api.add_resource(GetPayments, '/get_payments')
api.add_resource(GetPayment, '/get_payment')  # Changed this route to handle both payment ID and username
api.add_resource(AddPayment, '/add_payment')

api.add_resource(GetResources, '/get_job_resources') 
api.add_resource(GetResource, '/get_job_resource')  # Changed this route to handle ID, job name, or resource type
api.add_resource(AddResource, '/add_job_resource')
api.add_resource(UpdateResource, '/update_job_resource/<int:resource_id>')
api.add_resource(DeleteResource, '/delete_job_resource/<int:resource_id>')

api.add_resource(GetApplications, '/get_applications')
api.add_resource(GetApplication, '/get_application')  # Changed this route to handle application ID, username, or job name
api.add_resource(AddApplication, '/add_application')

if __name__ == "__main__":
    app.run(debug=True)