import aiohttp
import ssl
import certifi
import logging
import os

async def web_search_node(state):
    """Function to perform web search about a company using Perplexity API"""
    company_name = state.get('company_name', '')
    if not company_name:
        return {"error": "Company name is required"}
    
    search_question = f"What are the main products, services, and recent news about {company_name}? Focus on business-relevant information."
    
    
    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "llama-3.1-sonar-huge-128k-online",
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": search_question},
        ],
        "return_citations": True,
    }
    api_key = os.getenv('PERPLEXITY_API_KEY')
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}",
    }

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, headers=headers, ssl=ssl_context
            ) as response:
                response_json = await response.json()

        assistant_content = response_json["choices"][0]["message"]["content"]
        citations = response_json["citations"]

        combined_response = f"{assistant_content} {' '.join(citations)}"

        return {"response": combined_response}
    except aiohttp.ClientConnectorCertificateError as e:
        logging.error(f"SSL Certificate error: {e}")
        return {
            "error": "Unable to perform internet search due to SSL certificate issue. Please check your local SSL configuration."
        }
    except Exception as e:
        logging.error(f"Error during internet search: {e}")
        return {"error": f"An error occurred during the internet search: {str(e)}"}
