from flask import Flask, request, jsonify,render_template
import requests
from variables import CONFIG
from storageutils import MySQLManager

app = Flask(__name__)
app_id = '32585e1e'
app_key = '0051d9d4f45385f0ba6350587ded9a1b'

def store_jobs_in_db(job):
    query = """INSERT INTO jobs (job_id, job_title, company, category, description, date_posted, location, contract_type, salary)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
    values = (
        job.get('id',''),
        job.get('title', ''),
        job.get('company', {}).get('display_name', ''),
        job.get('category', {}).get('label', ''),
        job.get('description', ''),
        job.get('created', ''),
        job.get('location', {}).get('display_name', ''),
        job.get('contract_time', ''),  # Use '' as default value if key is missing
        job.get('salary_min', None)
    )
    try:
        MySQLManager.execute_query(query, values, **CONFIG['database']['vjit'])
    except Exception as error:
        print(f"Error storing job {job.get('id', 'unknown')}: {error}")



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/jobs', methods=['GET'])
def get_jobs():
    # Retrieve query parameters from request
    country = request.args.get('country')  # No default value, should be provided by the user
    page = request.args.get('page', '1')  # Default to page 1 if not provided

    # Check if country is provided
    if not country:
        return jsonify({'error': 'Country is required'}), 400

    # Define the Adzuna API endpoint
    url = f'https://api.adzuna.com/v1/api/jobs/{country}/search/{page}'

    # Set up the parameters with your API credentials
    params = {
        'app_id': app_id,
        'app_key': app_key,
    }

    # Set the headers to request JSON data
    headers = {
        'Accept': 'application/json'
    }

    try:
        # Make the API request
        response = requests.get(url, params=params, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            
            data = response.json()
            jobs = data.get('results', [])
            for job in jobs:
                store_jobs_in_db(job)  # Store each job individually
              # Return the full response
            return jsonify(data)
        else:
            # Return error details from the API response
            return jsonify({'error': response.json()}), response.status_code
    except requests.RequestException as e:
        # Handle request exceptions
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5006, debug=True)
