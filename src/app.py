from flask import Flask, redirect, request, jsonify,render_template, url_for,flash
from variables import CONFIG
from storageutils import MySQLManager
import uuid
from flask import send_file
import io
import os

app = Flask(__name__)


app.secret_key = os.urandom(24)

class User:
    def __init__(self, name, email, password, role):
        self.name = name
        self.email = email
        self.password = password
        self.role = role

    def insert(self, db_manager):
        try:
            query = "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)"
            db_manager.execute_query(query, (self.name, self.email, self.password, self.role), **CONFIG['database']['vjit'])
            print("Successfully registered")
            return True

        except Exception as e:
            print(f"Error while inserting data: {e}")
            return False
    def log(self, db_manager):
        try:
            query = "SELECT * FROM users WHERE email = %s"
            results = db_manager.execute_query(query, (self.email,), **CONFIG['database']['vjit'])

            for result in results:
                stored_password = result['password']
                stored_role = result['role']

                if stored_password == self.password:
                    self.role = stored_role  # Save the role for later use
                    print("Successfully logged in")
                    return True

            print("Invalid credentials")
            return False
        except Exception as e:
            print(f"Error while logging in: {e}")
            return False
        

def generate_application_id():
    # Generate a unique ID using UUID
    return str(uuid.uuid4())

@app.route('/',methods=['GET'])
def home():
    return render_template('home.html')

@app.route("/redirect_to_registration", methods=['GET','POST'])
def redirect_to_registration():
    return render_template("registration.html")

@app.route("/redirect_to_login", methods=['GET', 'POST'])
def redirect_to_login():
    return render_template("login.html")

@app.route("/emp_dash", methods=['GET', 'POST'])
def emp_dash():
    return render_template("emp.html")


@app.route('/upload_job', methods=['POST','GET'])
def upload_job():
    if request.method == 'POST':
        job_id = request.form.get('job_id')
        job_title = request.form.get('job_title')
        company = request.form.get('company')
        category = request.form.get('category')
        description = request.form.get('description')
        date_posted = request.form.get('date_posted')
        location = request.form.get('location')
        contract_time = request.form.get('contract_time')
        salary = request.form.get('salary')
        country = request.form.get('country')
        
        if not all([job_id, job_title, company, category, description, date_posted, location, contract_time, salary, country]):
            flash("Please fill all fields!", "danger")
            return redirect(url_for('upload_job'))

        else:
            query = """INSERT INTO jobs (job_id, job_title, company, category, description, date_posted, location, contract_type, salary, country) 
                  VALUES (%s, %s, %s, %s,%s,%s,%s,%s,%s,%s)"""
            MySQLManager.execute_query(query, (job_id, job_title, company, category, description, date_posted, location, contract_time, salary, country), **CONFIG['database']['vjit'])
            flash("Job successfully uploaded!", "success")
            return redirect(url_for('upload_job'))
    if request.method=='GET':
        return render_template("job_upload.html")


@app.route("/review_application", methods=['GET', 'POST'])
def review_application():
    query = "SELECT * FROM application where status='pending'"
    applications = MySQLManager.execute_query(query,(), **CONFIG['database']['vjit'])
    return render_template("review.html", applications=applications)


@app.route("/update_application_status/<application_id>/<action>", methods=['POST'])#todoo
def update_application_status(application_id, action):
    new_status = "application accepted" if action == "accept" else "rejected"
    query = "UPDATE application SET status = %s WHERE application_id = %s"
    MySQLManager.execute_query(query, (new_status, application_id), **CONFIG['database']['vjit'])
    flash(f"Application ID {application_id} has been {new_status}.")  # Flash message
    return redirect(url_for("review_applications"))


@app.route("/view_resume/<application_id>")
def view_resume(application_id):
    query = "SELECT resume FROM application WHERE application_id = %s"
    result = MySQLManager.execute_query(query, (application_id,), **CONFIG['database']['vjit'])

    if result:
        resume_data = result[0]['resume']
        return send_file(io.BytesIO(resume_data), mimetype='application/pdf', as_attachment=False)
    else:
        return "Resume not found", 404
        
@app.route("/user_dash", methods=['GET', 'POST'])
def user_dash():
    return render_template("user.html")

@app.route("/track_application", methods=['GET', 'POST'])
def track_application():
     if request.method == "POST":
         tracking_id=request.form.get("tracking-id")
         query="SELECT status FROM application WHERE application_id = %s"
         result=MySQLManager.execute_query(query,(tracking_id,),**CONFIG['database']['vjit'])
         if result:
            status = result[0]['status']
            return render_template('track.html', status=status)
         else:
            status = "Tracking ID not found"
            return render_template('track.html', status=status)
    
     return render_template('track.html', status=None)

@app.route("/registration", methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        role=request.form.get('role')#role
        password = request.form.get('password')
        conpass = request.form.get('confirm-password')
        
# Check if passwords match
        if conpass != password:
            return "Passwords do not match"

        user = User(name, email, password, role)
        if user.insert(MySQLManager):
            return redirect(url_for("redirect_to_login"))
    return render_template("registration.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
       
        user = User(None, email, password, None)
        
        if user.log(MySQLManager):
            # Redirect based on role saved during login
            if user.role == 'user':
                return redirect(url_for("user_dash"))
            else:
                return redirect(url_for("emp_dash"))
        else:
            return "Invalid credentials"
    return render_template("login.html")


@app.route('/countries')
def countries():
    return render_template('countries.html')

@app.route('/explore_jobs', methods=['POST'])
def explore_jobs():
    # Retrieve form data
    country = request.form.get('country')
    category = request.form.get('category')

    query = """
    SELECT * FROM jobs
    WHERE country = %s AND category = %s
    """
    values=(country,category)
    jobs = MySQLManager.execute_query(query, values,**CONFIG['database']['vjit'])
    return render_template('p3.html', country=country, category=category,jobs=jobs)

@app.route("/success", methods=['GET','POST'])
def success():
    application_id = request.args.get('application_id')
    return render_template("success.html", application_id=application_id)


@app.route('/application', methods=['GET', 'POST'])
def application():
    job_id=request.args.get('job_id')
    if request.method == 'POST':  
        # Handle form submission
        name = request.form.get('full-name')
        email = request.form.get('email-id')
        mobile = request.form.get('mobile-no')
        salary = request.form.get('expected-salary')
        loc = request.form.get('current-location')
        resume = request.files['resume-upload']
        resume_data = resume.read()

        # Generate a unique application ID
        application_id = generate_application_id()

        query = """
        insert into application (application_id,job_id,name,email,mobile,salary,location,resume) values (%s,%s,%s,%s,%s,%s,%s,%s)
        """ 
        values=(application_id,job_id,name,email,mobile,salary,loc,resume_data)
        MySQLManager.execute_query(query, values,**CONFIG['database']['vjit'])

        # Render the success page with application ID
        print(application_id)
        return redirect(url_for('success', application_id=application_id))
    
    # Render the application form
    return render_template('application.html')


if __name__=="__main__":
    app.run(port=5009,debug=True)
