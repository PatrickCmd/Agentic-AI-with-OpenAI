import os
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import PyPDF2
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

# Load environment variables
_ = load_dotenv(find_dotenv())

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def create_vector_store(store_name: str) -> dict:
    """
    Create a new vector store in OpenAI.
    
    Args:
        store_name: Name for the vector store
        
    Returns:
        dict: Details of the created vector store
    """
    try:
        vector_store = client.vector_stores.create(name=store_name)
        details = {
            "id": vector_store.id,
            "name": vector_store.name,
            "created_at": vector_store.created_at,
            "file_count": vector_store.file_counts.completed
        }
        return details
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return {}

def get_vector_store_details(vector_store_id: str) -> dict:
    """
    Get details about a vector store.
    
    Args:
        vector_store_id: ID of the vector store
        
    Returns:
        dict: Details of the vector store
    """
    try:
        vector_store = client.vector_stores.retrieve(vector_store_id=vector_store_id)
        details = {
            "id": vector_store.id,
            "name": vector_store.name,
            "created_at": vector_store.created_at,
            "file_count": vector_store.file_counts.completed
        }
        return details
    except Exception as e:
        print(f"Error retrieving vector store: {e}")
        return {}

def upload_single_file(file_path: str, vector_store_id: str):
    """
    Upload a single file to a vector store.
    
    Args:
        file_path: Path to the file
        vector_store_id: ID of the vector store
        
    Returns:
        dict: Status of the upload
    """
    file_name = os.path.basename(file_path)
    try:
        file_response = client.files.create(file=open(file_path, 'rb'), purpose="assistants")
        attach_response = client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_response.id
        )
        return {"file": file_name, "status": "success", "file_id": file_response.id}
    except Exception as e:
        print(f"Error with {file_name}: {str(e)}")
        return {"file": file_name, "status": "failed", "error": str(e)}

def upload_files_to_vector_store(file_paths: list, vector_store_id: str):
    """
    Upload multiple files to a vector store in parallel.
    
    Args:
        file_paths: List of file paths
        vector_store_id: ID of the vector store
        
    Returns:
        dict: Stats about the upload
    """
    stats = {"total_files": len(file_paths), "successful_uploads": 0, "failed_uploads": 0, "errors": []}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(upload_single_file, file_path, vector_store_id): file_path for file_path in file_paths}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result["status"] == "success":
                stats["successful_uploads"] += 1
            else:
                stats["failed_uploads"] += 1
                stats["errors"].append(result)

    return stats

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Extracted text
    """
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return text

def query_vector_store(vector_store_id: str, query: str, max_results: int = 5):
    """
    Query a vector store.
    
    Args:
        vector_store_id: ID of the vector store
        query: Query string
        max_results: Maximum number of results
        
    Returns:
        list: Search results
    """
    try:
        response = client.vector_stores.search(
            vector_store_id=vector_store_id,
            query=query,
            max_num_results=max_results
        )
        return response
    except Exception as e:
        print(f"Error querying vector store: {e}")
        return None
