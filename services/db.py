import sqlite3
import os
from datetime import datetime

# Use /home for Azure App Service persistent storage, fallback to local for dev
if os.path.exists('/home'):
    # Azure App Service - use persistent /home mount
    DB_DIR = '/home/data'
    os.makedirs(DB_DIR, exist_ok=True)
    DB_PATH = os.path.join(DB_DIR, 'jobs.db')
else:
    # Local development
    DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'jobs.db')

# Demo job data - hardcoded for all users
DEMO_JOBS = [
    {
        'title': 'Senior Python Developer',
        'company': 'TechCorp Inc.',
        'location': 'Remote',
        'pay': '$120,000 - $160,000',
        'posting_date': '2025-02-01',
        'description': 'We are looking for an experienced Python developer to join our growing team. 5+ years of experience required. Work on backend systems and APIs.'
    },
    {
        'title': 'Full Stack Web Developer',
        'company': 'WebSolutions LLC',
        'location': 'San Francisco, CA',
        'pay': '$100,000 - $140,000',
        'posting_date': '2025-02-05',
        'description': 'Build scalable web applications with React, Node.js, and PostgreSQL. Work on cutting-edge projects. 3+ years experience.'
    },
    {
        'title': 'Data Scientist',
        'company': 'DataDriven AI',
        'location': 'New York, NY',
        'pay': '$130,000 - $180,000',
        'posting_date': '2025-02-08',
        'description': 'Join our ML team. Experience with Python, TensorFlow, and AWS required. Build machine learning models for production.'
    },
    {
        'title': 'DevOps Engineer',
        'company': 'CloudMasters',
        'location': 'Austin, TX',
        'pay': '$110,000 - $150,000',
        'posting_date': '2025-02-06',
        'description': 'Manage CI/CD pipelines, Kubernetes, and cloud infrastructure. 3+ years of DevOps experience. Docker and Terraform skills needed.'
    },
    {
        'title': 'Frontend Developer (React)',
        'company': 'DesignStudio Pro',
        'location': 'Los Angeles, CA',
        'pay': '$90,000 - $130,000',
        'posting_date': '2025-02-04',
        'description': 'Create beautiful, responsive UIs with React and TypeScript. Strong focus on user experience. 2+ years React experience.'
    },
    {
        'title': 'Software Architect',
        'company': 'Enterprise Solutions',
        'location': 'Boston, MA',
        'pay': '$140,000 - $180,000',
        'posting_date': '2025-02-07',
        'description': 'Design large-scale systems. 10+ years of software development experience. Leadership skills required. Microservices architecture.'
    },
    {
        'title': 'Java Backend Engineer',
        'company': 'FinTech Innovations',
        'location': 'New York, NY',
        'pay': '$115,000 - $155,000',
        'posting_date': '2025-02-09',
        'description': 'Build robust backend services with Java and Spring Boot. 4+ years experience. Financial systems knowledge a plus.'
    },
    {
        'title': 'Cloud Architect',
        'company': 'CloudSync Corp',
        'location': 'Seattle, WA',
        'pay': '$135,000 - $175,000',
        'posting_date': '2025-02-08',
        'description': 'Design and implement cloud infrastructure solutions. AWS, Azure, or GCP expertise required. 6+ years experience.'
    },
    {
        'title': 'Mobile App Developer (iOS)',
        'company': 'AppCreators Inc.',
        'location': 'Remote',
        'pay': '$95,000 - $135,000',
        'posting_date': '2025-02-07',
        'description': 'Develop native iOS applications with Swift. 3+ years iOS development experience. App Store deployment knowledge.'
    },
    {
        'title': 'Android Developer',
        'company': 'MobileTech Solutions',
        'location': 'Mountain View, CA',
        'pay': '$100,000 - $140,000',
        'posting_date': '2025-02-06',
        'description': 'Build Android apps with Kotlin and Java. 3+ years Android experience. Play Store publishing experience required.'
    },
    {
        'title': 'Machine Learning Engineer',
        'company': 'AI Research Labs',
        'location': 'Berkeley, CA',
        'pay': '$140,000 - $190,000',
        'posting_date': '2025-02-09',
        'description': 'Develop ML models for computer vision. PyTorch and TensorFlow expertise. PhD preferred, MSc acceptable.'
    },
    {
        'title': 'Security Engineer',
        'company': 'CyberShield Inc.',
        'location': 'Washington, DC',
        'pay': '$120,000 - $160,000',
        'posting_date': '2025-02-08',
        'description': 'Implement security protocols and penetration testing. 5+ years cybersecurity experience. CISSP certification preferred.'
    },
    {
        'title': 'Database Administrator',
        'company': 'DataFlow Systems',
        'location': 'Chicago, IL',
        'pay': '$105,000 - $145,000',
        'posting_date': '2025-02-07',
        'description': 'Manage and optimize PostgreSQL and MongoDB databases. 4+ years DBA experience. Query optimization expertise.'
    },
    {
        'title': 'QA Automation Engineer',
        'company': 'TestPro Solutions',
        'location': 'Remote',
        'pay': '$85,000 - $120,000',
        'posting_date': '2025-02-06',
        'description': 'Write automated tests with Selenium and Cypress. 3+ years QA automation experience. CI/CD pipeline knowledge.'
    },
    {
        'title': 'Go Developer',
        'company': 'SystemsCore',
        'location': 'Remote',
        'pay': '$110,000 - $150,000',
        'posting_date': '2025-02-09',
        'description': 'Build high-performance systems with Go. 2+ years Go experience. Concurrency and networking expertise.'
    },
    {
        'title': 'Rust Developer',
        'company': 'Systems Programming Co.',
        'location': 'Portland, OR',
        'pay': '$120,000 - $160,000',
        'posting_date': '2025-02-08',
        'description': 'Develop systems software with Rust. 2+ years Rust experience. Memory safety and performance optimization focus.'
    },
    {
        'title': 'TypeScript / Node.js Developer',
        'company': 'FullStack Tech',
        'location': 'Denver, CO',
        'pay': '$105,000 - $145,000',
        'posting_date': '2025-02-07',
        'description': 'Build scalable backend services with Node.js and TypeScript. 3+ years experience. Express.js or Nest.js knowledge.'
    },
    {
        'title': 'Vue.js Frontend Developer',
        'company': 'WebDynamics',
        'location': 'Austin, TX',
        'pay': '$95,000 - $135,000',
        'posting_date': '2025-02-06',
        'description': 'Build modern UIs with Vue.js 3. 2+ years Vue experience. State management with Vuex or Pinia.'
    },
    {
        'title': 'C++ Systems Engineer',
        'company': 'HighPerformance Systems',
        'location': 'Mountain View, CA',
        'pay': '$130,000 - $170,000',
        'posting_date': '2025-02-09',
        'description': 'Develop low-level systems software in C++. 5+ years C++ experience. Real-time systems knowledge.'
    },
    {
        'title': 'Python Data Engineer',
        'company': 'BigData Analytics',
        'location': 'Remote',
        'pay': '$115,000 - $155,000',
        'posting_date': '2025-02-08',
        'description': 'Design data pipelines with Python, Spark, and Kafka. 4+ years data engineering experience. ETL pipeline expertise.'
    },
    {
        'title': 'GraphQL Developer',
        'company': 'API Innovations',
        'location': 'San Francisco, CA',
        'pay': '$105,000 - $145,000',
        'posting_date': '2025-02-07',
        'description': 'Build GraphQL APIs and backend services. 2+ years GraphQL experience. Apollo or Hasura knowledge.'
    },
    {
        'title': 'Infrastructure as Code Engineer',
        'company': 'CloudOps Pro',
        'location': 'Remote',
        'pay': '$120,000 - $160,000',
        'posting_date': '2025-02-06',
        'description': 'Write infrastructure code with Terraform and CloudFormation. 4+ years IaC experience. AWS and multi-cloud expertise.'
    },
    {
        'title': 'Blockchain Developer',
        'company': 'CryptoTech Labs',
        'location': 'Remote',
        'pay': '$125,000 - $165,000',
        'posting_date': '2025-02-09',
        'description': 'Develop smart contracts with Solidity. 2+ years blockchain experience. Ethereum and Web3 knowledge required.'
    },
    {
        'title': 'Game Developer (C#/Unity)',
        'company': 'GameStudio Interactive',
        'location': 'Los Angeles, CA',
        'pay': '$100,000 - $140,000',
        'posting_date': '2025-02-08',
        'description': 'Create games with Unity and C#. 3+ years game development experience. 3D graphics and physics engine knowledge.'
    },
    {
        'title': 'Technical Product Manager',
        'company': 'TechProduct Ventures',
        'location': 'New York, NY',
        'pay': '$130,000 - $170,000',
        'posting_date': '2025-02-07',
        'description': 'Lead technical product strategy. 5+ years product/engineering experience. Data-driven product development expertise.'
    },
]

def init_db():
    """Initialize SQLite database with demo jobs."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create jobs table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            pay TEXT,
            posting_date TEXT,
            description TEXT,
            skills TEXT DEFAULT 'unknown',
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert demo data if table is empty
    cursor.execute('SELECT COUNT(*) as count FROM jobs')
    if cursor.fetchone()['count'] == 0:
        for job in DEMO_JOBS:
            cursor.execute('''
                INSERT INTO jobs (title, company, location, pay, posting_date, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (job['title'], job['company'], job['location'], job['pay'], job['posting_date'], job['description']))
    
    conn.commit()
    conn.close()
    
    # Ensure all required columns exist
    ensure_columns_exist()

def ensure_columns_exist():
    """Check if all required columns exist in jobs table, add them if not."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(jobs)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Define required columns and their definitions
    required_columns = {
        'user_id': 'TEXT',
        'created_at': 'TIMESTAMP',
        'updated_at': 'TIMESTAMP',
        'skills': "TEXT DEFAULT 'unknown'",
        'link': 'TEXT',
        'applied': 'INTEGER DEFAULT 0'
    }
    
    # Add missing columns
    for column_name, column_def in required_columns.items():
        if column_name not in existing_columns:
            try:
                cursor.execute(f'ALTER TABLE jobs ADD COLUMN {column_name} {column_def}')
                print(f"[DB] Added missing column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"[DB] Error adding column {column_name}: {e}")
    
    conn.commit()
    conn.close()

def get_all_jobs(include_demo=False):
    """Retrieve all jobs from database. Excludes demo data by default."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if include_demo:
        cursor.execute('SELECT * FROM jobs ORDER BY posting_date DESC')
    else:
        # Exclude demo jobs (those with NULL user_id)
        cursor.execute('SELECT * FROM jobs WHERE user_id IS NOT NULL ORDER BY posting_date DESC')
    
    jobs = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jobs

def get_demo_jobs():
    """Retrieve only demo jobs (those with NULL user_id)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM jobs WHERE user_id IS NULL ORDER BY posting_date DESC')
    jobs = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jobs

def get_job_by_id(job_id):
    """Retrieve a specific job by ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
    job = cursor.fetchone()
    
    conn.close()
    return dict(job) if job else None

def get_user_jobs(user_id):
    """Retrieve all jobs created by a specific user."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    jobs = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jobs

def save_job(title, company, location, pay, description, user_id, skills='unknown', posting_date=None, link=None):
    """Save a new job to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if posting_date is None:
        posting_date = datetime.now().strftime('%Y-%m-%d')
    
    # Default skills to 'unknown' if not provided or empty
    if not skills:
        skills = 'unknown'
    
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO jobs (title, company, location, pay, posting_date, description, skills, user_id, link, applied, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    ''', (title, company, location, pay, posting_date, description, skills, user_id, link, now, now))
    
    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    
    return job_id

def update_job(job_id, title, company, location, pay, description):
    """Update an existing job."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute('''
        UPDATE jobs 
        SET title = ?, company = ?, location = ?, pay = ?, description = ?, updated_at = ?
        WHERE id = ?
    ''', (title, company, location, pay, description, now, job_id))
    
    conn.commit()
    conn.close()

def delete_job(job_id, user_id):
    """Delete a job. Only allows deletion if job belongs to the user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Only delete if the job belongs to this user (prevents deleting demo jobs or other users' jobs)
    cursor.execute('DELETE FROM jobs WHERE id = ? AND user_id = ?', (job_id, user_id))
    
    rows_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    return rows_deleted > 0

def toggle_applied(job_id, user_id):
    """Toggle the applied status of a job. Only allows if job belongs to the user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get current applied status
    cursor.execute('SELECT applied FROM jobs WHERE id = ? AND user_id = ?', (job_id, user_id))
    row = cursor.fetchone()
    
    if row is None:
        conn.close()
        return None
    
    # Toggle the status
    new_status = 0 if row[0] else 1
    cursor.execute('UPDATE jobs SET applied = ? WHERE id = ? AND user_id = ?', (new_status, job_id, user_id))
    
    conn.commit()
    conn.close()
    
    return new_status
def execute_sql_query(query):
    """
    Execute a SQL query safely. Only allows SELECT queries (read-only).
    Returns a dict with results and column names, or error message.
    """
    # Strip whitespace and convert to uppercase for checking
    query_stripped = query.strip()
    query_upper = query_stripped.upper()
    
    # Security: Only allow SELECT queries to prevent accidental data modification
    if not query_upper.startswith('SELECT'):
        return {
            'error': 'Only SELECT queries are allowed in developer mode.'
        }
    
    # Additional security check - block some dangerous patterns
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'TRUNCATE', 'CREATE', 'EXEC']
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return {
                'error': f'The keyword "{keyword}" is not allowed in developer mode.'
            }
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        cursor.execute(query)
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Fetch all results
        rows = cursor.fetchall()
        
        # Convert Row objects to dictionaries
        results = [dict(row) for row in rows]
        
        conn.close()
        
        return {
            'results': results,
            'columns': columns
        }
    except sqlite3.Error as e:
        return {
            'error': str(e)
        }
    except Exception as e:
        return {
            'error': f'An error occurred: {str(e)}'
        }

def query_jobs_with_filters(filters):
    """
    Query jobs with filters using a safe query builder approach.
    Filters is a list of dicts with 'column' and 'value' keys.
    Example: [{'column': 'title', 'value': 'developer'}, {'column': 'location', 'value': 'remote'}]
    """
    # Allowed columns to prevent SQL injection
    ALLOWED_COLUMNS = ['id', 'title', 'description', 'skills', 'location', 'pay', 'company', 'posting_date', 'user_id', 'applied']
    
    # Validate filters
    if not filters or len(filters) == 0:
        return {
            'error': 'At least one filter is required'
        }
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Start with basic SELECT
        query = 'SELECT * FROM jobs WHERE '
        conditions = []
        params = []
        
        for filter_obj in filters:
            column = filter_obj.get('column', '').strip().lower()
            value = filter_obj.get('value', '').strip()
            
            # Validate column name
            if column not in ALLOWED_COLUMNS:
                conn.close()
                return {
                    'error': f'Invalid column: {column}'
                }
            
            if not value:
                continue
            
            # Use LIKE for case-insensitive substring matching
            conditions.append(f'{column} LIKE ?')
            params.append(f'%{value}%')
        
        if not conditions:
            conn.close()
            return {
                'error': 'At least one filter value is required'
            }
        
        # Combine conditions with AND
        query += ' AND '.join(conditions)
        
        cursor.execute(query, params)
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Fetch all results (limit to 100 for safety)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows[:100]]
        
        conn.close()
        
        return {
            'results': results,
            'columns': columns
        }
    except sqlite3.Error as e:
        return {
            'error': str(e)
        }
    except Exception as e:
        return {
            'error': f'An error occurred: {str(e)}'
        }