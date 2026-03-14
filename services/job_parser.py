"""
Job Parser Module
Uses Gemini AI to extract structured job information from job posting text.
"""
import google.generativeai as genai
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Gemini API - Job Parser uses dedicated API key
GEMINI_JOB_PARSER_API_KEY = os.getenv('GEMINI_JOB_PARSER_API_KEY')
if not GEMINI_JOB_PARSER_API_KEY:
    raise ValueError("GEMINI_JOB_PARSER_API_KEY is not set in environment variables")

genai.configure(api_key=GEMINI_JOB_PARSER_API_KEY)

# Initialize model - dynamically select free-tier supported model
job_parser_model = None
try:
    available_models = genai.list_models()
    generative_models = [m for m in available_models if 'generateContent' in m.supported_generation_methods]
    
    if generative_models:
        model_name = generative_models[0].name
        logger.info(f"Job Parser using Gemini model: {model_name}")
        job_parser_model = genai.GenerativeModel(model_name)
    else:
        logger.error("No generative models found with generateContent support")
except Exception as e:
    logger.error(f"Error listing or initializing Gemini models: {str(e)}")
    logger.info("Attempting to use gemini-1.5-flash as fallback...")
    try:
        job_parser_model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        logger.error("Failed to initialize job parser model")

# System prompt for job parsing
SYSTEM_PROMPT = """You are an expert job posting analyzer. Your task is to extract and normalize structured information from job posting text.

Extract the following fields from the job posting:
1. title - The job title/position name
2. company - The company name
3. location - Format location using these rules:
   - If fully remote: return exactly "Remote"
   - If hybrid with location: return "City, St - Hybrid" (e.g., "San Francisco, CA - Hybrid")
   - If on-site: return "City, St" (e.g., "San Francisco, CA")
4. pay - Return a single number as the LOWER end of the salary range (as a number, not string). 
   Examples: if "$100,000-$150,000" return 100000, if "$60k-$80k" return 60000, if "Competitive" return null
5. description - A concise 2-3 sentence summary of the role and key responsibilities
6. skills - A comma-separated list of the most important technical skills and keywords required (e.g., "Python, AWS, Docker, Kubernetes")
7. certificates - Required certifications (e.g., "AWS Solutions Architect, Security+, CISSP"). Return null if none listed.
8. category - Job category/type. Choose from: Cybersecurity, DevOps, Backend, Frontend, Data Science, Help Desk, Cloud, QA, Mobile, Systems, Other
9. seniority - Experience level. Choose from: Junior, Mid-level, Senior, Lead, Entry-level
10. experience_required - Years of experience required as a number (e.g., 5). Return null if not specified.
11. tech_stack - Main technology stack/frameworks (e.g., "Python, Django, PostgreSQL, AWS")
12. industry - Industry sector (e.g., Finance, Healthcare, SaaS, E-commerce, Tech)
13. link - The URL/link to the job posting if provided. Return null if not found.

Return ONLY a valid JSON object with these exact keys. If a field is not found, use null.
Example response format:
{
    "title": "Senior Software Engineer",
    "company": "Tech Company Inc.",
    "location": "San Francisco, CA - Hybrid",
    "pay": 150000,
    "description": "Lead the development of cloud infrastructure. Build scalable systems using Python and AWS. 5+ years experience required.",
    "skills": "Python, AWS, Docker, Kubernetes, Cloud Architecture",
    "certificates": null,
    "category": "Backend",
    "seniority": "Senior",
    "experience_required": 5,
    "tech_stack": "Python, FastAPI, PostgreSQL, AWS",
    "industry": "Tech",
    "link": null
}"""


def parse_job_posting(job_text):
    """
    Parse job posting text using Gemini AI.
    
    Args:
        job_text (str): The raw job posting text
        
    Returns:
        dict: Extracted job information or error dict
    """
    try:
        print(f"\n[JOB_PARSER] Parsing job posting ({len(job_text)} characters)...")
        
        # Use the dynamically selected free-tier model
        if not job_parser_model:
            raise ValueError("Job parser model not initialized")
        
        # Create the prompt
        prompt = f"{SYSTEM_PROMPT}\n\nJob Posting:\n{job_text}"
        
        # Generate response
        response = job_parser_model.generate_content(prompt)
        
        # Parse the JSON response
        response_text = response.text.strip()
        print(f"[JOB_PARSER] Raw response: {response_text[:200]}...")
        
        # Handle markdown code blocks
        if response_text.startswith('```json'):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith('```'):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith('```'):
            response_text = response_text[:-3]  # Remove trailing ```
        
        response_text = response_text.strip()
        
        job_data = json.loads(response_text)
        
        print(f"[JOB_PARSER] Successfully parsed job posting")
        print(f"[JOB_PARSER] Title: {job_data.get('title')}")
        print(f"[JOB_PARSER] Company: {job_data.get('company')}")
        print(f"[JOB_PARSER] Location: {job_data.get('location')}")
        print(f"[JOB_PARSER] Pay: {job_data.get('pay')}")
        
        return job_data
        
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse Gemini response as JSON: {str(e)}"
        print(f"[JOB_PARSER] ERROR: {error_msg}")
        logger.error(error_msg)
        return {
            'error': 'parse_error',
            'message': error_msg
        }
        
    except Exception as e:
        error_msg = f"Error parsing job posting: {str(e)}"
        print(f"[JOB_PARSER] ERROR: {error_msg}")
        logger.error(error_msg)
        return {
            'error': 'parsing_error',
            'message': error_msg
        }


def validate_job_data(job_data):
    """
    Validate the parsed job data.
    
    Args:
        job_data (dict): The parsed job data
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ['title', 'company', 'location', 'description']
    
    for field in required_fields:
        if not job_data.get(field):
            print(f"[JOB_PARSER] ⚠ Missing required field: {field}")
            return False
    
    return True
