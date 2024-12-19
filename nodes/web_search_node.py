import aiohttp
import ssl
import certifi
import logging
import os
import asyncio

def sync_web_search_node(state):
    """Synchronous wrapper for web_search_node"""
    return asyncio.run(web_search_node(state))

async def web_search_node(state):
    """Function to perform web search about a company using Perplexity API"""
    print(state)
    
    search_question = f"""Find comprehensive financial and business information about {state}, including:
    1. Executive summary and company overview
    2. Key financial metrics (Income statement, balance sheet, cash flow highlights)
    3. Management analysis and future outlook
    4. ESG initiatives and corporate governance
    5. Risk factors and regulatory compliance
    6. Notable business segments and performance
    7. Recent financial ratios, capital expenditure, and investments
    
    Focus on the most recent annual report data and verified financial information."""

    
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
        state["final_doc"] = combined_response
        state["word_count"] = len(combined_response.split())
        state["llm_name"] = "perplexity-llama-3.1"
        print("Internet web search results are ")
        if "graph" in state:
            state["graph"].add_node("web_search", 
                                  data={"type": "web_search",
                                       "content": combined_response})
        
        return state
    except aiohttp.ClientConnectorCertificateError as e:
        logging.error(f"SSL Certificate error: {e}")
        return {
            "error": "Unable to perform internet search due to SSL certificate issue. Please check your local SSL configuration."
        }
    except Exception as e:
        logging.error(f"Error during internet search: {e}")
        return {"error": f"An error occurred during the internet search: {str(e)}"}
