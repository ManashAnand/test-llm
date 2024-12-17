import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from LLMs.llm import LLM

# Load the write prompt template
with open(os.path.join(os.path.dirname(__file__), 'prompts', 'write.txt'), 'r') as file:
    write_template = file.read()

# Create a ChatPromptTemplate
write_prompt = ChatPromptTemplate([
    ('user', write_template)
    ])

# Create the write chain
write_chain = write_prompt | LLM | StrOutputParser()

if __name__ == "__main__":
    # Test the write_chain
    test_instruction = """Write a detailed financial analysis report for [Company Name]'s Q4 2023 performance, focusing on key financial metrics, business highlights, and future outlook. The report should be comprehensive, data-driven, and include relevant industry comparisons."""

    test_plan = "Section 1 - Main Point: Executive Summary and Key Financial Highlights - Word Count: 250 words"

    test_text = "In Q4 2023, [Company Name] demonstrated robust financial performance, marked by significant revenue growth and improved operational efficiency across key business segments."
  
    # Invoke the write_chain
    result = write_chain.invoke({
        "intructions": test_instruction,
        "plan": test_plan,
        "text": test_text,
        "STEP": "Paragraph 1"
    })
    
    # Print the result
    print("Generated Paragraph:")
    print(result)
