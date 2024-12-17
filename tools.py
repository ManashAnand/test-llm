
import requests
import json
import os
import re



def write_markdown_file(content, filename):
  """Writes the given content as a markdown file to the local directory.

  Args:
    content: The string content to write to the file.
    filename: The filename to save the file as.
  """
  with open(f"{filename}.md", "w") as f:
    f.write(content)
    
    
    
  


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
        "research_context": research_content,
        "plan": plan,
        "initial_prompt": initial_prompt,
        "num_steps": state.get('num_steps', 0) + 1,
        "company_info": structured_data.get('company_names', []),
        "industry": structured_data.get('industry'),
        "competitors": structured_data.get('competitors', []),
        "shareholders": structured_data.get('shareholders', []),
        "market_position": structured_data.get('market_position')
    }