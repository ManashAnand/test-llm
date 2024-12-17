import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LLMs.llm import LLM

from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import pdfplumber

# Load the plan prompt template

def read_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    print(text)
    print("#######################################################################################")
    return text

# with open(os.path.join(os.path.dirname(__file__), 'prompts', 'plan.txt'), 'r') as file:
#     plan_template = file.read()

pdf_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # Go up one directory
    'input.pdf'
)
plan_template = read_pdf(pdf_path)
# Create a PromptTemplate
plan_prompt = ChatPromptTemplate([
        ('user', plan_template)
    ])


plan_chain = plan_prompt | LLM | StrOutputParser()


## For testing
if __name__ == "__main__":
    # Test the plan_chain
    test_instruction = "Create a comprehensive financial analysis report for Q4 2023, focusing on market trends, key performance indicators, and investment opportunities. Include detailed analysis of market volatility, sector performance, and provide strategic recommendations with supporting data and rationale."
    
    # Invoke the plan_chain
    result = plan_chain.invoke({"intructions": test_instruction})
    
    # Print the result
    print("Generated Writing Plan:")
    print(result)


