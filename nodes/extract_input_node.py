
import os
import pdfplumber
import os
import logging
from textwrap import dedent
from pdf2image import convert_from_path
from PIL import Image
import aiohttp
import asyncio
from typing import List, Optional

import tempfile
import shutil

from tools.tools import extract_text_from_image_vision_async, summarize_file_text_async
from clients.openai.client import async_openai_client as async_client

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
    
async def download_file(input_file_path: str, temp_dir: str, temp_files: List[str]) -> str:
    filename = os.path.basename(input_file_path)
    temp_file_path = os.path.join(temp_dir, filename)
    shutil.copy2(input_file_path, temp_file_path)
    temp_files.append(temp_file_path)
    
    download_dir = os.path.dirname(temp_file_path)
    print(f"File downloaded to directory: {download_dir}")
    
    return temp_file_path

async def process_input_file(input_file_path: str):
    logging.info(f"Attempting to download file from {input_file_path}")
    print(input_file_path)
    
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    input_doc_path = await download_file(input_file_path, temp_dir, temp_files)  
    print(input_doc_path)
    # input_doc_path = await download_file_async(input_file_path)
    # temp_files.append(input_doc_path)

    # # Determine document type from file content
    with open(input_doc_path, "rb") as f:
        magic_number = f.read(4)
    
    if magic_number == b"%PDF":
        print("got pdf here")
        images = convert_from_path(input_doc_path)
        tasks = []
        page_summaries = []
        
        for i, image in enumerate(images):
            image = image.resize((2048, 2048))
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_image_file:
                image.save(temp_image_file.name, format="PNG")
    #             # First get raw text
                raw_text = await extract_text_from_image_vision_async(temp_image_file.name, "")
                
    #             # Analyze page type
                system_message = dedent("""
                    Analyze this page and extract detailed financial information. Focus on:
                    - Revenue and profit figures
                    - Balance sheet items
                    - Cash flow statements
                    - Financial ratios
                    - Year-over-year comparisons
                    - Currency values and units
                    - Significant financial events or changes
                    
                    Output format:
                    FINANCIAL_TYPE: <type of financial information>
                    PERIOD: <time period>
                    KEY_METRICS:
                    - <metric1>: <value1>
                    - <metric2>: <value2>
                    NOTES: <any important context or observations>
                    """)
                
                response = await async_client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": raw_text},
                    ],
                )
                page_type = response.choices[0].message.content
                
    #             # Get detailed summary based on page type
                summary = await summarize_file_text_async(raw_text, page_type=page_type)
                page_summaries.append(f"=== Page {i+1} ===\n{page_type}\n{summary}")
        
        file_text = "\n\n".join(page_summaries)
        print(file_text)
                
    # elif magic_number == b"PK\x03\x04":
    #     print("Got .docx file here")


    #     raw_text = await process_docx(input_doc_path, temp_files)
        
        

    #     system_message = dedent("""
    #         Analyze this page and determine its type and key information focus. Types include:
    #         - COMPANY_INFO: Basic company details
    #         - SHAREHOLDER: Shareholder information
    #         - DIRECTOR: Director information
    #         - PEP: Politically Exposed Person information
    #         - FINANCIAL: Financial statements
    #         - OTHER: Other information
            
    #         Output format:
    #         PAGE_TYPE: <type>
    #         KEY_FOCUS: <brief description>
    #     """)

    #     response = await async_client.chat.completions.create(
    #         model="gpt-4o-2024-11-20",
    #         messages=[
    #             {"role": "system", "content": system_message},
    #             {"role": "user", "content": raw_text},
    #         ],
    #     )
    #     document_type = response.choices[0].message.content
    #     file_text = await summarize_file_text_async(raw_text, page_type=document_type)
        
        
    # elif magic_number[:2] == b"\xFF\xD8":
    #     logging.info("The file is identified as a JPEG.")
    #     from PIL import Image

    #     image = Image.open(input_doc_path)
    #     image = image.resize((2048, 2048))  

    #     # Extract text from the JPEG
    #     raw_text = await extract_text_from_image_vision_async(input_doc_path, "")
    #     logging.info(f"Extracted raw text from JPEG:\n{raw_text}")

    #     # Analyze page type and get summary
    #     system_message = dedent("""
    #         Analyze this page and determine its type and key information focus. Types include:
    #         - COMPANY_INFO: Basic company details
    #         - SHAREHOLDER: Shareholder information
    #         - DIRECTOR: Director information
    #         - PEP: Politically Exposed Person information
    #         - FINANCIAL: Financial statements
    #         - OTHER: Other information
            
    #         Output format:
    #         PAGE_TYPE: <type>
    #         KEY_FOCUS: <brief description>
    #     """)
    #     response = await async_client.chat.completions.create(
    #         model="gpt-4o-2024-11-20",
    #         messages=[
    #             {"role": "system", "content": system_message},
    #             {"role": "user", "content": raw_text},
    #         ],
    #     )
    #     page_type = response.choices[0].message.content
    #     summary = await summarize_file_text_async(raw_text, page_type=page_type)

    #     file_text = f"=== JPEG File ===\n{page_type}\n{summary}"
    

    # else:
    #     # Handle non-PDF files
    #     print("Got other here")
    #     raw_text = await extract_text_from_image_vision_async(input_doc_path, "")
    #     file_text = await summarize_file_text_async(raw_text)


def extract_data_from_pdf(state):
    print(state)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)  
    pdf_path = os.path.join(parent_dir, 'input.pdf')  
    asyncio.run(process_input_file(pdf_path))
    
    # pdf_content = read_pdf(pdf_path)
    # print(pdf_content)
    
# if __name__ == "__main__":
#     asyncio.run(extract_data_from_pdf())