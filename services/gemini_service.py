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
    Parse natural language query to extract filters, aggregations, and intent.
    Gemini intelligently determines what fields to analyze based on the question.
    
    Args:
        user_query: Natural language query from user
        
    Returns:
        Dictionary with:
        - filters: List of filter objects with column, operator, value
        - aggregation: Dict with type (average/sum/count/min/max/None) and field
        - intent: String describing analysis intent
    """
    if not model:
        logger.error("Gemini model not initialized")
        return {"error": "Gemini API not configured"}
    
    try:
        prompt = f"""Analyze this job search query and extract filters and aggregation needs.

User Query: "{user_query}"

Return ONLY a valid JSON object with NO code blocks, NO markdown, NO extra text:
{{
    "filters": [
        {{"column": "title", "operator": "LIKE", "value": "engineering"}},
        {{"column": "location", "operator": "LIKE", "value": "remote"}}
    ],
    "aggregation": {{
        "type": "average",
        "field": "pay"
    }},
    "intent": "salary_analysis"
}}

Rules:
- "filters": Array of filter objects. Map user intent to database columns:
  - Job titles/roles → column: "title"
  - Locations → column: "location"
  - Skills → column: "description" (search in job description)
  - Salary mentions → column: "pay"
  - Company names → column: "company"
  - operator: Always use "LIKE" for substring matching
  - value: The value they're searching for
- "aggregation": Set aggregation if query asks for stats:
  - type: "average", "sum", "count", "min", "max", or null if no aggregation
  - field: "pay" (salary), "posting_date" (recency), or null
- "intent": Short phrase describing what they want (e.g., "salary_analysis", "skill_comparison", "location_search")

Return ONLY the JSON object with no extra text."""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Remove markdown code block formatting if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        elif response_text.startswith('```python'):
            response_text = response_text[9:]
        elif response_text.startswith('```'):
            response_text = response_text[3:]
        
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse the JSON response
        try:
            result = json.loads(response_text)
            
            # Validate structure
            if 'filters' not in result:
                result['filters'] = []
            if 'aggregation' not in result:
                result['aggregation'] = {'type': None, 'field': None}
            if 'intent' not in result:
                result['intent'] = 'general_search'
            
            logger.info(f"Query parsed successfully: {json.dumps(result, indent=2)}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {response_text}")
            logger.error(f"JSON parse error: {str(e)}")
            return {"filters": [], "aggregation": {"type": None, "field": None}, "intent": "error"}
            
    except Exception as e:
        logger.error(f"Error parsing query with Gemini: {str(e)}", exc_info=True)
        return {"filters": [], "aggregation": {"type": None, "field": None}, "intent": "error"}


def analyze_jobs(jobs: list, user_query: str, parsed_filters: dict) -> str:
    """
    Use Gemini to analyze job data and provide insights.
    Handles aggregations (average salary, salary range, etc.) based on parsed intent.
    
    Args:
        jobs: List of job dictionaries matching the query
        user_query: Original user query
        parsed_filters: Parsed filters from parse_query()
        
    Returns:
        Analysis result string with insights and statistics
    """
    if not model:
        logger.error("Gemini model not initialized")
        return "Gemini API not configured"
    
    if not jobs:
        filter_summary = []
        if parsed_filters.get('filters'):
            for f in parsed_filters['filters']:
                filter_summary.append(f"{f.get('column')} = {f.get('value')}")
        criteria = ', '.join(filter_summary) if filter_summary else 'your search'
        return f"No jobs found matching your criteria: {criteria}"
    
    try:
        # Calculate aggregations if needed
        aggregation_stats = {}
        agg_config = parsed_filters.get('aggregation', {})
        
        if agg_config.get('type') and agg_config.get('field'):
            agg_type = agg_config['type']
            agg_field = agg_config['field']
            
            # Extract numeric values for the field
            values = []
            for job in jobs:
                value = job.get(agg_field)
                if value:
                    # Try to convert to float if it's a salary field
                    if agg_field == 'pay' and isinstance(value, str):
                        # Extract number from salary string (e.g., "$120,000" -> 120000)
                        import re
                        matches = re.findall(r'\d+', value.replace(',', ''))
                        if matches:
                            values.append(float(matches[0]))
                    elif isinstance(value, (int, float)):
                        values.append(float(value))
            
            # Perform aggregation calculations
            if values:
                if agg_type == 'average':
                    aggregation_stats['average'] = sum(values) / len(values)
                elif agg_type == 'sum':
                    aggregation_stats['sum'] = sum(values)
                elif agg_type == 'count':
                    aggregation_stats['count'] = len(values)
                elif agg_type == 'min':
                    aggregation_stats['min'] = min(values)
                elif agg_type == 'max':
                    aggregation_stats['max'] = max(values)
                
                # Add count automatically with other aggregations
                aggregation_stats['count'] = len(values)
                
                logger.info(f"Calculated {agg_type} for {agg_field}: {aggregation_stats}")
        
        # Prepare data for Gemini analysis
        jobs_summary = json.dumps(jobs[:10], indent=2)  # Limit to first 10 to save tokens
        
        # Build prompt with aggregation context
        aggregation_context = ""
        if aggregation_stats:
            stats_str = ", ".join([f"{k}: ${v:,.0f}" if k != 'count' else f"{k}: {v}" 
                                   for k, v in aggregation_stats.items()])
            aggregation_context = f"\n\nKey Statistics:\n{stats_str}"
        
        prompt = f"""Analyze these job postings and answer the user's question.

User Question: "{user_query}"

Number of matching jobs: {len(jobs)}
Sample Job Data:
{jobs_summary}{aggregation_context}

Provide a CONCISE answer (2-3 sentences max) that directly addresses their question:
- If asking about salary: Include the statistics and what that means
- If asking about locations/roles: Highlight patterns
- If asking for lists: Summarize key findings
- Be specific with numbers when relevant

Be direct and helpful. No lengthy explanations."""

        response = model.generate_content(prompt)
        summary = response.text.strip()
        
        # Remove markdown code block formatting if present
        if summary.startswith('```'):
            lines = summary.split('\n')
            if len(lines) > 1:
                summary = '\n'.join(lines[1:-1]) if lines[-1].strip() == '```' else '\n'.join(lines[1:])
        
        summary = summary.strip()
        logger.info(f"Job analysis completed for query: '{user_query}'")
        return summary
        
    except Exception as e:
        logger.error(f"Error analyzing jobs with Gemini: {str(e)}", exc_info=True)
        return f"Error analyzing data: {str(e)}"


def filter_jobs(jobs: list, filters: dict) -> list:
    """
    Filter jobs based on parsed filters.
    Supports new filter format with column, operator, value.
    
    Args:
        jobs: Full list of jobs
        filters: Parsed filters dict with 'filters' list
        
    Returns:
        Filtered list of jobs
    """
    filtered = jobs
    
    # Handle new filter format
    filter_list = filters.get('filters', [])
    
    for filter_obj in filter_list:
        column = filter_obj.get('column', '').lower()
        operator = filter_obj.get('operator', 'LIKE').upper()
        value = str(filter_obj.get('value', '')).lower()
        
        if not column or not value:
            continue
        
        # Apply filter based on operator and column
        if operator == 'LIKE':
            # Substring match (case-insensitive)
            filtered = [
                j for j in filtered
                if column in j and value in str(j[column]).lower()
            ]
            logger.info(f"Filtered by {column} LIKE '{value}': {len(filtered)} jobs remaining")
        
        elif operator == 'EQUALS':
            # Exact match (case-insensitive)
            filtered = [
                j for j in filtered
                if column in j and str(j[column]).lower() == value
            ]
            logger.info(f"Filtered by {column} = '{value}': {len(filtered)} jobs remaining")
        
        elif operator == 'GREATER':
            # Greater than
            try:
                threshold = float(value)
                filtered = [
                    j for j in filtered
                    if column in j and float(str(j[column]).replace(',', '')) > threshold
                ]
                logger.info(f"Filtered by {column} > {value}: {len(filtered)} jobs remaining")
            except ValueError:
                logger.warning(f"Could not convert '{value}' to number for {column} > comparison")
        
        elif operator == 'LESS':
            # Less than
            try:
                threshold = float(value)
                filtered = [
                    j for j in filtered
                    if column in j and float(str(j[column]).replace(',', '')) < threshold
                ]
                logger.info(f"Filtered by {column} < {value}: {len(filtered)} jobs remaining")
            except ValueError:
                logger.warning(f"Could not convert '{value}' to number for {column} < comparison")
    
    return filtered
