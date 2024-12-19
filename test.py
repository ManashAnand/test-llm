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
    
    app = create_workflow(LLM)
    
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
    
    pdf_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'input.pdf'
    )
    # pdf_content = read_pdf(pdf_path)
    
    context_files = {
        'financial_metrics': 'context/financial_metrics.txt',
        'industry_benchmarks': 'context/industry_benchmarks.txt',
        'previous_reports': 'context/previous_reports.txt'
    }
    
    context_data = {}
    for key, filepath in context_files.items():
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filepath)
        context_data[key] = read_context_file(full_path, default_contexts[key])
    
    combined_context = f"""
    Previous Financial Reports:
    {context_data['previous_reports']}
    
    Industry Benchmarks:
    {context_data['industry_benchmarks']}
    
    Key Financial Metrics:
    {context_data['financial_metrics']}
    """
    
    test_instruction = '''Write a comprehensive analysis of Company X's annual financial performance and market position, focusing on the following sections:

    1. Executive Summary
    - Overview of key financial highlights
    - Major developments during the period
    - Summary of performance metrics

    2. Company Overview
    - Business model and operations
    - Market presence and positioning
    - Key competitive advantages

    3. Financial Performance Analysis
    a. Income Statement
        - Revenue analysis and growth trends
        - Cost structure and margins
        - Profitability metrics
    
    b. Balance Sheet
        - Asset composition and quality
        - Liability structure
        - Working capital management
    
    c. Cash Flow Statement
        - Operating cash flows
        - Investment activities
        - Financing decisions

    4. Key Financial Metrics
    - Profitability ratios
    - Liquidity ratios
    - Solvency ratios
    - Efficiency ratios

    5. Segment-Wise Performance
    - Business segment analysis
    - Geographic segment analysis
    - Product/service line performance

    6. Risk Assessment
    - Market risks
    - Operational risks
    - Financial risks
    - Regulatory compliance

    7. Corporate Governance
    - Board composition and effectiveness
    - Internal controls
    - Compliance framework

    8. Sustainability and ESG Initiatives
    - Environmental impact
    - Social responsibility
    - Governance practices

    9. Strategic Initiatives
    - Capital expenditure
    - Investments and acquisitions
    - R&D initiatives
    - Digital transformation

    10. Future Outlook
        - Growth strategies
        - Market expansion plans
        - Financial projections
        - Industry trends

    Please provide detailed analysis supported by specific data points and comparative metrics where applicable.'''

    inputs = {
        "initial_prompt": test_instruction,
        "context": combined_context,
        "num_steps": 10,
        "llm_name": "llama3.1-8b-groq",
        "data": "pdf_content" or "No PDF content available"  
    }
    
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