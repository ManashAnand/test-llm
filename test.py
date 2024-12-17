import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LLMs.llm import LLM 
from graph import create_workflow
import pdfplumber

def read_pdf(pdf_path):
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
        return text
    except FileNotFoundError:
        print(f"Warning: PDF file {pdf_path} not found")
        return ""
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return ""

def read_context_file(context_path, default_content):
    try:
        with open(context_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Warning: Context file {context_path} not found, using default content")
        return default_content
    except Exception as e:
        print(f"Error reading context file {context_path}: {str(e)}")
        return default_content

def main():
    load_dotenv()
    
    # Create the workflow
    app = create_workflow(LLM)
    
    # Default content for each context type
    default_contexts = {
        'financial_metrics': """
Default Financial Metrics:
- Revenue Growth Rate
- Gross Margin
- Operating Margin
- EBITDA
- Return on Investment (ROI)
- Return on Equity (ROE)
""",
        'industry_benchmarks': """
Default Industry Benchmarks:
- Industry average performance metrics
- Market competition analysis
- Sector growth rates
- Risk factors
""",
        'previous_reports': """
Default Previous Report Structure:
- Executive Summary
- Financial Performance
- Market Position
- Future Outlook
"""
    }
    
    # 1. Read the PDF file (main data)
    pdf_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'input.pdf'
    )
    pdf_content = read_pdf(pdf_path)
    
    # 2. Read additional context files with fallbacks
    context_files = {
        'financial_metrics': 'context/financial_metrics.txt',
        'industry_benchmarks': 'context/industry_benchmarks.txt',
        'previous_reports': 'context/previous_reports.txt'
    }
    
    context_data = {}
    for key, filepath in context_files.items():
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filepath)
        context_data[key] = read_context_file(full_path, default_contexts[key])
    
    # 3. Combine context
    combined_context = f"""
    Previous Financial Reports:
    {context_data['previous_reports']}
    
    Industry Benchmarks:
    {context_data['industry_benchmarks']}
    
    Key Financial Metrics:
    {context_data['financial_metrics']}
    """
    
    test_instruction = '''Write a 10-word comprehensive analysis of Company X's annual financial performance and market position, focusing on key financial metrics, strategic initiatives, and future outlook.

Cover the following key areas:
1. **Financial Overview:** Analyze key financial statements (Income Statement, Balance Sheet, Cash Flow Statement), including year-over-year comparisons, key ratios, and significant trends in revenue, profitability, and cash flow management.

2. **Market Performance:** Examine stock performance, market capitalization changes, dividend history, and comparison with industry benchmarks and major competitors.

3. **Operational Analysis:** Evaluate operational efficiency metrics, segment-wise performance, geographical distribution of revenue, and key operational highlights of the fiscal year.

4. **Risk Assessment:** Detail major business risks, regulatory challenges, market uncertainties, and the company's risk mitigation strategies, including cybersecurity and compliance measures.

5. **Strategic Initiatives:** Review major strategic decisions, acquisitions, divestitures, R&D investments, and digital transformation efforts, analyzing their impact on business performance.

6. **ESG Performance:** Assess Environmental, Social, and Governance initiatives, sustainability metrics, corporate responsibility programs, and their alignment with long-term business objectives.

7. **Future Outlook:** Provide detailed analysis of growth strategies, market expansion plans, projected financial targets, and potential challenges or opportunities in the coming fiscal year.

8. **Industry Context:** Analyze broader industry trends, competitive landscape, technological disruptions, and their potential impact on the company's business model.'''

    
    inputs = {
        "initial_prompt": test_instruction,
        "context": combined_context,
        "num_steps": 10,
        "llm_name": "llama3.1-8b-groq",
        "data": pdf_content or "No PDF content available"  
    }
    
    # Print context being used (for debugging)
    print("\nUsing Context:")
    print("-" * 80)
    print(combined_context[:500] + "..." if len(combined_context) > 500 else combined_context)
    print("-" * 80)
    
    # Run the workflow
    print("\nGenerating response...")
    output = app.invoke(inputs)
    
    print("\nGenerated Response:")
    print("-" * 80)
    print(output.get('final_doc', "No content generated."))
    print("-" * 80)

if __name__ == "__main__":
    main()