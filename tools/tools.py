
import requests
import json
import os
import re
import base64
import logging, json
import aiofiles

from clients.openai.client import async_openai_client as async_client
from clients.openai.client import openai_client as client


def write_markdown_file(content, filename):
  """Writes the given content as a markdown file to the local directory.

  Args:
    content: The string content to write to the file.
    filename: The filename to save the file as.
  """
  with open(f"{filename}.md", "w") as f:
    f.write(content)
    
async def encode_image_async(image_path: str) -> str:
    async with aiofiles.open(image_path, "rb") as image_file:
        image_data = await image_file.read()
        return base64.b64encode(image_data).decode("utf-8")
    
async def extract_text_from_image_vision_async(image_path: str, checklist: str) -> str:
    base64_image = await encode_image_async(image_path)
    response = await async_client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Analyze this document and extract relevant information based on the following financials. Provide a summary of the extracted information:\n\n{checklist}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        max_tokens=1000,
    )
    return response.choices[0].message.content
  
  

async def summarize_file_text_async(raw_text: str, page_type: str = None, is_followup: bool = False):
    # Log the raw text before summarization
    logging.info("Raw text before summarization:")
    logging.info(raw_text)

    # Define specific prompts based on page type
    prompts = {
        "COMPANY_INFO": """
            Extract all company-related information including:
            - Company name
            - Registration details
            - Address
            - Contact information
            - Business type
            Present in a clear, structured format.
        """,
        "SHAREHOLDER": """
            Extract all shareholder information including:
            - Names
            - Ownership percentages
            - Types of shares
            - Nationality/jurisdiction
            - Any associated entities
            List each shareholder separately with complete details.
        """,
        "DIRECTOR": """
            Extract all director information including:
            - Full names
            - Positions
            - Appointment dates
            - Nationality
            - Other directorships
            List each director separately with complete details.
        """,
        "PEP": """
            Extract all PEP-related information including:
            - PEP status
            - Political connections
            - Risk assessments
            - Associated parties
            Note any potential red flags or concerns.
        """,
        "FINANCIAL": """
            Extract key financial information including:
            - Statement type
            - Period covered
            - Key metrics
            - Notable items
            Focus on accuracy of numerical data.
        """,
        "OTHER": """
            Extract all relevant information that could be useful for KYC purposes:
            - Any identifying information
            - Relationships
            - Key dates
            - Important declarations
            Note anything that could be relevant for compliance.
        """
    }

    # Select appropriate prompt based on page type
    system_message = prompts.get(page_type, prompts["OTHER"]) if page_type else dedent(
        """
        Extract all relevant information for KYC purposes, organizing it by type:
        - Company information
        - Individual details
        - Relationships
        - Financial information
        - Compliance-related data
        Present in a clear, structured format with appropriate sections.
        """
    )

    response = await async_client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Here is the text:\n{raw_text}"},
        ],
    )
    summary = response.choices[0].message.content

    logging.info("Summarized output:")
    logging.info(summary)

    return summary


def standardize_data(raw_data):
    """Standardize the extracted data into a consistent format"""
    try:
        if isinstance(raw_data, str):
            json_match = re.search(r'```json\s*(.*?)\s*```', raw_data, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                json_match = re.search(r'\{.*\}', raw_data, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    raise ValueError("No JSON data found")
        else:
            data = raw_data

        standardized = {
            "company_name": [],
            "industry": [],
            "competitors": [],
            "shareholders": [],
            "market_position": {}
        }

        company_keys = ["Company name(s)", "Company names", "company_name", "companies"]
        industry_keys = ["Industry", "industry", "sector", "Sector"]
        competitor_keys = ["Main competitors", "Competitors", "competitors", "Competition"]
        shareholder_keys = ["Key shareholders", "Shareholders", "shareholders", "Major shareholders"]
        market_position_keys = ["Market position", "market_position", "Position"]

        for key in company_keys:
            if key in data:
                value = data[key]
                if isinstance(value, str):
                    standardized["company_name"] = [name.strip() for name in value.split(',')]
                elif isinstance(value, list):
                    standardized["company_name"] = value
                break

        for key in industry_keys:
            if key in data:
                value = data[key]
                if isinstance(value, str):
                    standardized["industry"] = [value.strip()]
                elif isinstance(value, list):
                    standardized["industry"] = value
                break

        for key in competitor_keys:
            if key in data:
                value = data[key]
                if isinstance(value, str):
                    standardized["competitors"] = [comp.strip() for comp in value.split(',')]
                elif isinstance(value, list):
                    standardized["competitors"] = value
                break

        for key in shareholder_keys:
            if key in data:
                value = data[key]
                if isinstance(value, str):
                    if "not" in value.lower() and "mentioned" in value.lower():
                        standardized["shareholders"] = []
                    else:
                        standardized["shareholders"] = [share.strip() for share in value.split(',')]
                elif isinstance(value, list):
                    standardized["shareholders"] = value
                break

        for key in market_position_keys:
            if key in data:
                value = data[key]
                if isinstance(value, dict):
                    standardized["market_position"] = value
                elif isinstance(value, str):
                    standardized["market_position"] = {"description": value}
                break

        return standardized

    except Exception as e:
        print(f"Error standardizing data: {e}")
        return {
            "company_name": [],
            "industry": [],
            "competitors": [],
            "shareholders": [],
            "market_position": {}
        }

def perplexity_node(state):
    """Query Perplexity AI for additional context and research"""
    print("---GATHERING RESEARCH FROM PERPLEXITY---")
    
    
    api_key = os.getenv('PERPLEXITY_API_KEY')
    # print(api_key)
    url = "https://api.perplexity.ai/chat/completions"
    initial_prompt = state['initial_prompt']
    plan = state['plan']
    
    payload = {
       "model": "llama-3.1-sonar-small-128k-online", 
        "messages": [
            {
                "role": "system",
                "content": "You are a financial analysis assistant. Provide detailed research and analysis."
            },
            {
                "role": "user",
                "content": f"""Provide detailed research and context for the following financial analysis task:
                Task: {initial_prompt}
                Current Plan: {plan}
                Focus on recent market data, industry reports, and expert analysis."""
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1024,  
        "top_p": 0.9
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print("*"*80)
    response = requests.request("POST", url, json=payload, headers=headers)
    
    response_data = json.loads(response.text)
    research_content = response_data['choices'][0]['message']['content']
    print(research_content)
    
    
    payload2 = {
        "model": "llama-3.1-sonar-small-128k-online", 
        "messages": [
            {
                "role": "system",
                "content": "You are a financial analysis assistant. Extract and provide detailed research and analysis."
            },
            {
                "role": "user",
                "content": f"""Analyze the following financial context and extract key information:
                Task: {initial_prompt}
                Current Plan: {plan}
                
                Please provide your response in two parts:
                1. Structured Data (in JSON format):
                   - Company name(s)
                   - Industry
                   - Main competitors
                   - Key shareholders (if mentioned)
                   - Market position
                
                2. Detailed Analysis:
                   Focus on recent market data, industry reports, and expert analysis."""
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1024,  
        "top_p": 0.9
    }

    
    print("*"*80)
    print("Extracting data from context\n")
    response_ext = requests.request("POST", url, json=payload2, headers=headers)
    
    response_ext_data = json.loads(response_ext.text)
    extracted_data = response_ext_data['choices'][0]['message']['content']
    print(extracted_data)
    
    
    
    structured_data = standardize_data(extracted_data)
    print("Standardized data xyz")
    print(structured_data)
    print(structured_data.get('company_names', []))
    print(structured_data.get('industry', ''))
    print(structured_data.get('competitors', []))
    print(structured_data.get('shareholders', []))
    print(structured_data.get('market_position', ''))
    
    return {
          **state, 
        "research_context": research_content,
        "plan": plan,
        "initial_prompt": initial_prompt,
        "num_steps": state.get('num_steps', 0) + 1,
        "company_info": structured_data.get('company_names', []),
        "industry": structured_data.get('industry'),
        "competitors": structured_data.get('competitors', []),
        "shareholders": structured_data.get('shareholders', []),
        "market_position": structured_data.get('market_position'),
           "num_steps": state.get('num_steps', 0) + 1
    }