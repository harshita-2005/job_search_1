from flask import Flask, redirect, request, jsonify,render_template, url_for
from variables import CONFIG
from storageutils import MySQLManager
import uuid

app = Flask(__name__)

def generate_application_id():
    # Generate a unique ID using UUID
    return str(uuid.uuid4())

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/countries')
def index():
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
        return render_template('success.html', application_id=application_id)
    
    # Render the application form
    return render_template('application.html')


if __name__=="__main__":
    app.run(host='0.0.0.0',port=5009,debug=True)
