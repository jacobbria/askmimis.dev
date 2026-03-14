from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import logging
from dotenv import load_dotenv
from services import db, gemini_service, auth, job_parser

# Load environment variables
load_dotenv()

# Load API keys
gemini_key = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Configure logging - safe for gunicorn multi-worker environment
if __name__ != '__main__':
    # In production (gunicorn), let gunicorn handle logging
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    logger = app.logger
else:
    # In development, use basicConfig
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

# Initialize database on startup
db.init_db()

@app.route('/')
def index():
    """Home page with greeting and demo data button."""
    logger.info("Index page accessed")
    is_authenticated = auth.is_authenticated(session)
    return render_template('index.html', is_authenticated=is_authenticated)

@app.route('/login')
def login():
    """Login page with authentication and guest options."""
    is_authenticated = auth.is_authenticated(session)
    if is_authenticated:
        # Already logged in, redirect to jobs
        return redirect(url_for('jobs'))
    return render_template('login.html')

@app.route('/jobs')
def jobs():
    """Main jobs page with Direct Search and Gemini AI analysis."""
    logger.info("Jobs page accessed")
    is_authenticated = auth.is_authenticated(session)
    # Jobs page requires authentication OR guest mode
    # Guest mode verification will be done on frontend via localStorage
    user_id = session.get('user_id') if is_authenticated else None
    return render_template('jobs_beta.html', is_authenticated=is_authenticated, user_id=user_id)

@app.route('/jobs-classic')
def jobs_classic():
    """Legacy jobs page - kept for backward compatibility."""
    logger.info("Classic jobs page accessed")
    is_authenticated = auth.is_authenticated(session)
    try:
        if is_authenticated:
            user_id = session.get('user_id')
            jobs_list = db.get_user_jobs(user_id)
            logger.info(f"Retrieved {len(jobs_list)} jobs for user: {user_id}")
            return render_template('jobs.html', jobs=jobs_list, is_authenticated=is_authenticated, user_jobs=True)
        else:
            jobs_list = db.get_demo_jobs()
            logger.info(f"Retrieved {len(jobs_list)} demo jobs for unauthenticated user")
            return render_template('jobs.html', jobs=jobs_list, is_authenticated=is_authenticated, user_jobs=False)
    except Exception as e:
        logger.error(f"Error loading jobs: {str(e)}", exc_info=True)
        return render_template('error.html', message='Error loading job data'), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_query():
    """API endpoint to analyze job postings based on natural language query."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        logger.info(f"Analysis query submitted: '{query}'")
        
        if not query:
            logger.warning("Empty query submitted")
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        # Parse the query using Gemini
        logger.info("Parsing natural language query with Gemini...")
        parsed_filters = gemini_service.parse_query(query)
        
        if 'error' in parsed_filters:
            logger.error(f"Error parsing query: {parsed_filters['error']}")
            return jsonify({'error': parsed_filters['error']}), 500
        
        logger.info(f"Parsed filters: {parsed_filters}")
        
        # Get all jobs (including demo jobs for consistency with other search endpoints)
        all_jobs = db.get_all_jobs(include_demo=True)
        logger.info(f"Retrieved {len(all_jobs)} total jobs from database")
        
        # Filter jobs based on parsed criteria
        filtered_jobs = gemini_service.filter_jobs(all_jobs, parsed_filters)
        logger.info(f"After filtering: {len(filtered_jobs)} jobs match the criteria")
        
        # Use Gemini to analyze the filtered jobs
        logger.info("Analyzing filtered jobs with Gemini...")
        analysis = gemini_service.analyze_jobs(filtered_jobs, query, parsed_filters)
        
        logger.info(f"Analysis completed successfully for query: '{query}'")
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'job_count': len(filtered_jobs),
            'filtered_jobs': filtered_jobs,
            'filters': parsed_filters
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing analysis query: {str(e)}", exc_info=True)
        return jsonify({'error': 'Analysis failed: ' + str(e)}), 500

@app.route('/api/get-user-jobs', methods=['GET'])
def get_user_jobs_api():
    """API endpoint to get jobs posted by the authenticated user."""
    try:
        is_authenticated = auth.is_authenticated(session)
        if not is_authenticated:
            logger.warning("Unauthorized attempt to access user jobs")
            return jsonify({'error': 'Not authenticated', 'jobs': []}), 401
        
        user_id = session.get('user_id')
        jobs = db.get_user_jobs(user_id)
        logger.info(f"Retrieved {len(jobs)} jobs for authenticated user: {user_id}")
        return jsonify({'jobs': jobs}), 200
    except Exception as e:
        logger.error(f"Error getting user jobs: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}', 'jobs': []}), 500

@app.route('/api/get-demo-jobs', methods=['GET'])
def get_demo_jobs_api():
    """API endpoint to get demo jobs for guests."""
    try:
        jobs = db.get_demo_jobs()
        logger.info(f"Retrieved {len(jobs)} demo jobs for guest user")
        return jsonify({'jobs': jobs}), 200
    except Exception as e:
        logger.error(f"Error getting demo jobs: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}', 'jobs': []}), 500

@app.route('/data')
def data_options():
    """Display options for querying or adding data."""
    is_authenticated = auth.is_authenticated(session)
    if not is_authenticated:
        logger.warning("Unauthenticated user tried to access data options page")
        return redirect(url_for('index'))
    
    logger.info(f"Data options page accessed by user: {session.get('user_id')}")
    return render_template('data_options.html', is_authenticated=is_authenticated)

@app.route('/jobs/add')
def add_job():
    """Show the job input form."""
    is_authenticated = auth.is_authenticated(session)
    if not is_authenticated:
        logger.warning("Unauthenticated user tried to access job input page")
        return redirect(url_for('login'))
    
    logger.info(f"Job input form accessed by user: {session.get('user_id')}")
    return render_template('add_job.html', is_authenticated=is_authenticated)

@app.route('/jobs/parse', methods=['POST'])
def parse_job():
    """Parse a job posting using AI."""
    is_authenticated = auth.is_authenticated(session)
    if not is_authenticated:
        logger.warning("Unauthenticated user tried to parse job")
        return jsonify({'error': 'unauthorized', 'message': 'Please log in first'}), 401
    
    try:
        data = request.get_json()
        job_text = data.get('jobText', '').strip()
        
        if not job_text:
            logger.warning("Empty job text submitted for parsing")
            return jsonify({'error': 'empty', 'message': 'Job posting text cannot be empty'}), 400
        
        if len(job_text) < 50:
            logger.warning(f"Job text too short: {len(job_text)} characters")
            return jsonify({'error': 'too_short', 'message': 'Job posting must be at least 50 characters'}), 400
        
        logger.info(f"Parsing job posting ({len(job_text)} chars) by user: {session.get('user_id')}")
        
        # Parse the job posting
        parsed_job = job_parser.parse_job_posting(job_text)
        
        if 'error' in parsed_job:
            logger.error(f"Error parsing job: {parsed_job}")
            return jsonify(parsed_job), 500
        
        # Check for missing fields but allow partial data
        required_fields = ['title', 'company', 'location', 'description']
        missing_fields = [field for field in required_fields if not parsed_job.get(field)]
        
        if missing_fields:
            logger.warning(f"Parsed job has missing fields: {missing_fields}. Data: {parsed_job}")
            parsed_job['warning'] = f"Some fields were not extracted: {', '.join(missing_fields)}. Please fill them in manually."
        else:
            logger.info(f"Job parsing successful: {parsed_job.get('title')}")
        
        # Return parsed data regardless of missing fields (user can fill them in manually)
        return jsonify(parsed_job), 200
        
    except Exception as e:
        logger.error(f"Error parsing job: {str(e)}", exc_info=True)
        return jsonify({'error': 'parsing_error', 'message': 'Failed to parse job posting'}), 500

@app.route('/jobs/review')
def review_job():
    """Show the job review/edit form."""
    is_authenticated = auth.is_authenticated(session)
    if not is_authenticated:
        logger.warning("Unauthenticated user tried to access job review page")
        return redirect(url_for('index'))
    
    logger.info(f"Job review page accessed by user: {session.get('user_id')}")
    return render_template('review_job.html', is_authenticated=is_authenticated)

@app.route('/jobs/save', methods=['POST'])
def save_job():
    """Save a verified job posting to the database."""
    is_authenticated = auth.is_authenticated(session)
    if not is_authenticated:
        logger.warning("Unauthenticated user tried to save job")
        return jsonify({'error': 'unauthorized', 'message': 'Please log in first'}), 401
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'company', 'location', 'description']
        for field in required_fields:
            if not data.get(field, '').strip():
                logger.warning(f"Missing required field in job save: {field}")
                return jsonify({
                    'error': 'missing_field',
                    'message': f"Missing required field: {field}"
                }), 400
        
        user_id = session.get('user_id')
        logger.info(f"Saving job: {data.get('title')} by user: {user_id}")
        
        # Save to database
        job_id = db.save_job(
            title=data['title'].strip(),
            company=data['company'].strip(),
            location=data['location'].strip(),
            pay=data.get('pay', '').strip() or None,
            description=data['description'].strip(),
            skills=data.get('skills', 'unknown').strip() or 'unknown',
            user_id=user_id,
            link=data.get('link', '').strip() or None,
            certificates=data.get('certificates', '').strip() or None,
            category=data.get('category', '').strip() or None,
            seniority=data.get('seniority', '').strip() or None,
            experience_required=int(data['experience_required']) if data.get('experience_required') else None,
            tech_stack=data.get('tech_stack', '').strip() or None,
            industry=data.get('industry', '').strip() or None
        )
        
        logger.info(f"Job saved successfully with ID: {job_id}")
        return jsonify({
            'success': True,
            'message': 'Job posted successfully',
            'job_id': job_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error saving job: {str(e)}", exc_info=True)
        return jsonify({'error': 'save_error', 'message': 'Failed to save job'}), 500

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    """Display details for a specific job."""
    logger.info(f"Job detail page accessed for job ID: {job_id}")
    is_authenticated = auth.is_authenticated(session)
    user_id = session.get('user_id') if is_authenticated else None
    try:
        job = db.get_job_by_id(job_id)
        if not job:
            logger.warning(f"Job not found for ID: {job_id}")
            return render_template('error.html', message='Job not found'), 404
        logger.info(f"Successfully retrieved job: {job.get('title')}")
        is_owner = is_authenticated and job.get('user_id') == user_id
        return render_template('job_detail.html', job=job, is_authenticated=is_authenticated, is_owner=is_owner)
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {str(e)}", exc_info=True)
        return render_template('error.html', message='Error loading job details'), 500

@app.route('/jobs/delete/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    """Delete a job entry. Only the owner can delete their job."""
    is_authenticated = auth.is_authenticated(session)
    if not is_authenticated:
        logger.warning("Unauthenticated user tried to delete a job")
        return jsonify({'error': 'unauthorized', 'message': 'You must be logged in'}), 401
    
    try:
        user_id = session.get('user_id')
        logger.info(f"User {user_id} attempting to delete job {job_id}")
        
        success = db.delete_job(job_id, user_id)
        
        if success:
            logger.info(f"Job {job_id} deleted successfully by user {user_id}")
            return jsonify({'success': True, 'message': 'Job deleted successfully'})
        else:
            logger.warning(f"Job {job_id} not found or not owned by user {user_id}")
            return jsonify({'error': 'not_found', 'message': 'Job not found or you do not have permission to delete it'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'delete_error', 'message': 'Failed to delete job'}), 500

@app.route('/jobs/toggle-applied/<int:job_id>', methods=['POST'])
def toggle_applied(job_id):
    """Toggle the applied status of a job."""
    is_authenticated = auth.is_authenticated(session)
    if not is_authenticated:
        logger.warning("Unauthenticated user tried to toggle applied status")
        return jsonify({'error': 'unauthorized', 'message': 'You must be logged in'}), 401
    
    try:
        user_id = session.get('user_id')
        logger.info(f"User {user_id} toggling applied status for job {job_id}")
        
        new_status = db.toggle_applied(job_id, user_id)
        
        if new_status is not None:
            logger.info(f"Job {job_id} applied status toggled to {new_status} by user {user_id}")
            return jsonify({'success': True, 'applied': new_status})
        else:
            logger.warning(f"Job {job_id} not found or not owned by user {user_id}")
            return jsonify({'error': 'not_found', 'message': 'Job not found or you do not have permission'}), 404
            
    except Exception as e:
        logger.error(f"Error toggling applied status for job {job_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'toggle_error', 'message': 'Failed to update status'}), 500

@app.route('/health')
def health():
    """Health check endpoint for load balancer probe."""
    logger.debug("Health check endpoint called")
    return 'OK', 200

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.path}")
    return render_template('error.html', message='Page not found'), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"500 server error: {str(error)}", exc_info=True)
    return render_template('error.html', message='Server error'), 500

# ===== Authentication Routes =====

@app.route('/auth/login')
def auth_login():
    """Initiates Entra ID login flow."""
    print("\n[LOGIN] ===== AUTH LOGIN INITIATED =====")
    print(f"[LOGIN] Getting authorization URL from MSAL...")
    logger.info("User initiated login")
    auth_url = auth.get_auth_url()
    print(f"[LOGIN] Authorization URL generated")
    print(f"[LOGIN] Redirecting to: {auth_url[:100]}...")
    return redirect(auth_url)


@app.route('/auth/callback')
def auth_callback():
    """Handles Entra ID callback after user authentication."""
    try:
        print("\n[CALLBACK] ===== AUTH CALLBACK RECEIVED =====")
        code = request.args.get('code')
        session_state = request.args.get('session_state')
        error = request.args.get('error')
        error_description = request.args.get('error_description')
        
        print(f"[CALLBACK] URL Parameters:")
        print(f"[CALLBACK] Code: {code[:50]}..." if code else "[CALLBACK] No code")
        print(f"[CALLBACK] Session State: {session_state}")
        print(f"[CALLBACK] Error: {error}")
        print(f"[CALLBACK] Error Description: {error_description}")
        
        if error:
            print(f"[CALLBACK] ERROR from Microsoft: {error} - {error_description}")
            logger.warning(f"Auth error from Microsoft: {error} - {error_description}")
            return redirect(url_for('index'))
        
        if not code:
            print(f"[CALLBACK] No authorization code received in callback")
            logger.warning("No authorization code received in callback")
            return redirect(url_for('index'))
        
        print(f"[CALLBACK] Exchanging code for token...")
        # Exchange code for token
        token_response = auth.acquire_token_by_auth_code(code)
        
        print(f"[CALLBACK] Token response keys: {token_response.keys() if isinstance(token_response, dict) else 'Not a dict'}")
        
        if 'error' in token_response:
            print(f"[CALLBACK] Token acquisition FAILED")
            print(f"[CALLBACK] Error: {token_response.get('error')}")
            print(f"[CALLBACK] Description: {token_response.get('error_description')}")
            logger.error(f"Token acquisition failed: {token_response.get('error_description')}")
            return redirect(url_for('index'))
        
        print(f"[CALLBACK] Token acquired successfully!")
        # Store token in session
        session['access_token'] = token_response.get('access_token')
        session['user_id'] = token_response.get('id_token_claims', {}).get('oid')
        session['user_name'] = token_response.get('id_token_claims', {}).get('name')
        
        print(f"[CALLBACK] Stored in session:")
        print(f"[CALLBACK] - Access Token: {'Yes' if session.get('access_token') else 'No'}")
        print(f"[CALLBACK] - User ID: {session.get('user_id')}")
        print(f"[CALLBACK] - User Name: {session.get('user_name')}")
        
        logger.info(f"User authenticated successfully: {session.get('user_name')}")
        print(f"[CALLBACK] Authentication successful! Redirecting to home page...")
        return redirect(url_for('index'))
        
    except Exception as e:
        print(f"[CALLBACK] EXCEPTION in auth callback:")
        print(f"[CALLBACK] Exception Type: {type(e).__name__}")
        print(f"[CALLBACK] Exception Message: {str(e)}")
        import traceback
        print(f"[CALLBACK] Traceback:\n{traceback.format_exc()}")
        logger.error(f"Error in auth callback: {str(e)}", exc_info=True)
        return redirect(url_for('index'))


@app.route('/auth/logout')
def auth_logout():
    """Logs out the user by clearing session."""
    session.clear()
    logger.info("User logged out")
    return redirect(url_for('index'))


@app.route('/api/auth/status')
def auth_status():
    """API endpoint to check authentication status."""
    is_authenticated = auth.is_authenticated(session)
    user_name = session.get('user_name', 'Unknown User') if is_authenticated else None
    
    return jsonify({
        'authenticated': is_authenticated,
        'user_name': user_name,
        'user_id': session.get('user_id') if is_authenticated else None
    }), 200

@app.route('/api/execute-sql', methods=['POST'])
def execute_sql():
    """API endpoint for executing SQL queries in developer mode."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Execute the query through db module
        result = db.execute_sql_query(query)
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error executing SQL query: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/query-jobs', methods=['POST'])
def query_jobs():
    """API endpoint for querying jobs using the query builder."""
    try:
        data = request.get_json()
        filters = data.get('filters', [])
        
        if not filters:
            return jsonify({'error': 'No filters provided'}), 400
        
        # Query jobs with filters through db module
        result = db.query_jobs_with_filters(filters)
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error querying jobs: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/get-all-jobs', methods=['GET'])
def get_all_jobs():
    """API endpoint to get all jobs from the database."""
    try:
        jobs = db.get_all_jobs(include_demo=True)
        return jsonify({'jobs': jobs}), 200
    except Exception as e:
        logger.error(f"Error getting all jobs: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    # Note: In production, use Gunicorn instead of Flask's development server
    # gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
    logger.info("Starting Flask application on 0.0.0.0:8000")
    app.run(host='0.0.0.0', port=8000, debug=False)
