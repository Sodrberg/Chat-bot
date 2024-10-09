from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStoreRetriever
from langchain.chains import RetrievalQA
import os
import json
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv
import logging

load_dotenv()
openai_api_key = os.environ.get('OPENAI_API_KEY')
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')


@dataclass
class Document:
    page_content: str
    metadata: dict


def chunk_text(text: str) -> List[str]:
    """
    Splits the input text into chunks based on double newline separators.
    """
    pages = text.split('\n\n')
    chunks = [page.strip() for page in pages if page.strip()]
    return chunks


def process_json_files(directory_path: str) -> FAISS:
    """
    Processes all JSON files in the specified directory, extracts text from 'content',
    chunks the text, and embeds the chunks using OpenAIEmbeddings.

    Args:
        directory_path (str): Path to the directory containing JSON files.

    Returns:
        FAISS: The FAISS vector store containing embedded documents.
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")  # Retained the original model
    all_docs = []
    problematic_files = []

    for filename in os.listdir(directory_path):
        if filename.endswith('.json'):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if 'content' in item and isinstance(item['content'], list):
                                for content in item['content']:
                                    if content.get('type') == 'text':
                                        text = content.get('text', '')
                                        chunks = chunk_text(text)
                                        for i, chunk in enumerate(chunks):
                                            metadata = {
                                                'id': item.get('id'),
                                                'chunk_index': i,
                                                'total_chunks': len(chunks),
                                                'source_file': filename
                                            }
                                            doc = Document(page_content=chunk, metadata=metadata)
                                            all_docs.append(doc)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from file {file_path}: {e}")
                    problematic_files.append(file_path)
                    continue

    if not all_docs:
        error_message = "No documents found to embed."
        if problematic_files:
            error_message += f" Problematic files: {', '.join(problematic_files)}"
        raise ValueError(error_message)

    library = FAISS.from_documents(all_docs, embeddings)
    return library


def save_faiss_index(library: FAISS, save_directory: str, index_name: str = "faiss_index"):
    os.makedirs(save_directory, exist_ok=True)
    full_path = os.path.join(save_directory, index_name)
    try:
        library.save_local(save_directory, index_name)
        print(f"FAISS index saved to {full_path}")
        if os.path.exists(full_path):
            print(f"Verified: File exists at {full_path}")
            print(f"File size: {os.path.getsize(full_path)} bytes")
        else:
            print(f"Warning: File not found at {full_path} after saving")
        print(f"Contents of {save_directory}:")
        for item in os.listdir(save_directory):
            item_path = os.path.join(save_directory, item)
            print(f"  - {item} ({os.path.getsize(item_path)} bytes)")
    except Exception as e:
        print(f"Error saving FAISS index: {str(e)}")
        raise


def load_faiss_index(save_directory: str, index_name: str, embeddings_model: OpenAIEmbeddings) -> FAISS:
    full_path = os.path.join(save_directory, index_name)
    print(f"Attempting to load FAISS index from: {full_path}")
    
    if not os.path.exists(full_path) and not os.path.exists(full_path + '.faiss'):
        print(f"FAISS index file not found at: {full_path} or {full_path}.faiss")
        print(f"Contents of {save_directory}:")
        for item in os.listdir(save_directory):
            print(f"  - {item}")
        raise FileNotFoundError(f"FAISS index file not found at: {full_path} or {full_path}.faiss")

    try:
        library = FAISS.load_local(save_directory, embeddings_model, index_name=index_name, allow_dangerous_deserialization=True)
        print(f"FAISS index successfully loaded from {full_path}")
        return library
    except Exception as e:
        print(f"Error loading FAISS index: {str(e)}")
        raise


def query_vector_db(query: str, library: FAISS, top_k: int = 5) -> Optional[List[Document]]:
    """
    Queries the FAISS vector store with the user query.

    Args:
        query (str): The user's query.
        library (FAISS): The FAISS vector store containing embedded documents.
        top_k (int): The number of top results to return.

    Returns:
        Optional[List[Document]]: The top_k most relevant documents or None if no results.
    """
    query_answers = library.similarity_search(query, k=top_k)

    if not query_answers:
        print("No relevant answers found.")
        return None

    return query_answers


def update_faiss_index(combined_content):
    try:
        # Generate embeddings for the new content
        embeddings = generate_embeddings(combined_content)
        
        # Load existing index
        index_path = "path/to/your/faiss_index/file"
        index = faiss.read_index(index_path)
        
        # Add new embeddings to the index
        index.add(embeddings)
        
        # Save updated index
        faiss.write_index(index, index_path)
        logging.info(f"FAISS index updated successfully at {index_path}")
    except Exception as e:
        logging.error(f"Error updating FAISS index: {str(e)}")
        raise