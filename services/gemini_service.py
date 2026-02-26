import google.generativeai as genai
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
model = None

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    try:
        # List available models and pick the best one
        available_models = genai.list_models()
        generative_models = [m for m in available_models if 'generateContent' in m.supported_generation_methods]
        
        if generative_models:
            # Try to use the latest/best model
            model_name = generative_models[0].name
            logger.info(f"Using Gemini model: {model_name}")
            model = genai.GenerativeModel(model_name)
        else:
            logger.error("No generative models found with generateContent support")
    except Exception as e:
        logger.error(f"Error listing or initializing Gemini models: {str(e)}")
        logger.info("Attempting to use gemini-2.0-flash as fallback...")
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
        except:
            logger.error("Failed to initialize any Gemini model")
else:
    logger.warning("GEMINI_API_KEY not found in environment variables")


def parse_query(user_query: str) -> dict:
    """
    Parse natural language query to extract filters and intent.
    
    Args:
        user_query: Natural language query from user
        
    Returns:
        Dictionary with extracted filters and analysis intent
    """
    if not model:
        logger.error("Gemini model not initialized")
        return {"error": "Gemini API not configured"}
    
    try:
        prompt = f"""Analyze this job search query and extract relevant filters.
        
User Query: "{user_query}"

Return a JSON object with:
- job_title: The job title or role they're looking for (string or null)
- location: The location they're interested in (string or null)
- skills: Array of specific skills they mentioned
- seniority: Level (junior, mid, senior) or null
- intent: What analysis they want (e.g., "find top skills", "compare jobs", "salary analysis")
- salary_range: Any salary mentions (string or null)

Return ONLY valid JSON, no markdown formatting, no code blocks, no extra text."""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Remove markdown code block formatting if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]  # Remove ```json
        elif response_text.startswith('```'):
            response_text = response_text[3:]  # Remove ```
        
        if response_text.endswith('```'):
            response_text = response_text[:-3]  # Remove trailing ```
        
        response_text = response_text.strip()
        
        # Parse the JSON response
        try:
            result = json.loads(response_text)
            logger.info(f"Query parsed successfully: {result}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {response_text}")
            logger.error(f"JSON parse error: {str(e)}")
            return {"error": "Failed to parse query"}
            
    except Exception as e:
        logger.error(f"Error parsing query with Gemini: {str(e)}", exc_info=True)
        return {"error": str(e)}


def analyze_jobs(jobs: list, user_query: str, parsed_filters: dict) -> str:
    """
    Use Gemini to analyze job data and provide insights.
    
    Args:
        jobs: List of job dictionaries matching the query
        user_query: Original user query
        parsed_filters: Parsed filters from parse_query()
        
    Returns:
        Analysis result string
    """
    if not model:
        logger.error("Gemini model not initialized")
        return "Gemini API not configured"
    
    if not jobs:
        location = parsed_filters.get('location')
        title = parsed_filters.get('job_title')
        criteria = ', '.join([f for f in [title, location] if f])
        return f"No jobs found matching your criteria: {criteria if criteria else 'your search'}"
    
    try:
        jobs_summary = json.dumps(jobs, indent=2)
        
        prompt = f"""Analyze these job postings and answer the user's specific question.

User Question: "{user_query}"

Job Postings Data:
{jobs_summary}

Provide a BRIEF summary (2-3 sentences max) that directly answers their question. Focus on:
- Key findings
- Patterns observed
- Essential insights

Be concise and get straight to the point. No lengthy explanations."""

        response = model.generate_content(prompt)
        summary = response.text.strip()
        
        # Remove markdown code block formatting if present
        if summary.startswith('```'):
            # Find the closing ```
            lines = summary.split('\n')
            if len(lines) > 1:
                summary = '\n'.join(lines[1:-1]) if lines[-1].strip() == '```' else '\n'.join(lines[1:])
        
        summary = summary.strip()
        logger.info(f"Job analysis summary completed for query: '{user_query}'")
        return summary
        
    except Exception as e:
        logger.error(f"Error analyzing jobs with Gemini: {str(e)}", exc_info=True)
        return f"Error analyzing data: {str(e)}"


def filter_jobs(jobs: list, filters: dict) -> list:
    """
    Filter jobs based on parsed filters.
    
    Args:
        jobs: Full list of jobs
        filters: Parsed filters dict
        
    Returns:
        Filtered list of jobs
    """
    filtered = jobs
    
    # Filter by location (case-insensitive, substring match)
    if filters.get('location'):
        location = filters['location'].lower()
        filtered = [j for j in filtered if location in j['location'].lower()]
        logger.info(f"Filtered by location '{location}': {len(filtered)} jobs remaining")
    
    # Filter by job title (case-insensitive, substring match)
    if filters.get('job_title'):
        title = filters['job_title'].lower()
        filtered = [j for j in filtered if title in j['title'].lower()]
        logger.info(f"Filtered by title '{title}': {len(filtered)} jobs remaining")
    
    # Filter by skills mentioned in description
    if filters.get('skills') and len(filters['skills']) > 0:
        skill_keywords = [s.lower() for s in filters['skills']]
        filtered = [
            j for j in filtered 
            if any(skill in j['description'].lower() for skill in skill_keywords)
        ]
        logger.info(f"Filtered by skills {skill_keywords}: {len(filtered)} jobs remaining")
    
    return filtered
