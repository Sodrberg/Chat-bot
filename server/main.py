from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llamaparse_rag.llamaparse import LlamaParser
from graphrag_rag.graphrag1 import run_global_search
from fastapi.staticfiles import StaticFiles
from database.db_setup import init_db, get_db
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from database.models.user import User
from database.models.indexed_doc import IndexedDocument
from auth import get_user_id, get_password_hash, oauth2_scheme
from sqlalchemy import Select, Insert, Delete, Update
import subprocess
import re
import shutil
import os
import asyncio
from graphrag_rag.graphrag_local import run_local_search
from multimodal_rag.claud_image_analyze import ClaudeImageAnalyzer

from auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

# Import the pdf_to_images function
from multimodal_rag.pdf_to_images import pdf_to_images
from typing import Optional
from pathlib import Path
from multimodal_rag.claude_message_api import get_claude_recommendation

# Import the process and query functions for FAISS
from multimodal_rag.embed import (
    process_json_files, 
    query_vector_db, 
    save_faiss_index, 
    load_faiss_index
)

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS  # Ensure FAISS is imported

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # Initialize the database
    yield
    # Cleanup code (if any) goes here

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Adjust this to your React app's address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llama_parser = LlamaParser()

@app.post("/llamaparse/indexing")
async def parse_and_embed_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    allowed_content_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/html",
        "application/xml",
        "text/plain",
    ]

    if file.content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    try:
        index_id = await llama_parser.parse_and_embed_pdf(file)

        new_document = IndexedDocument(
            user_id=user_id,  # Use the user_id parameter here
            document_name=file.filename,
            index_id=index_id,
            indexing_method="llamaparse"
        )

        db.add(new_document)
        db.commit()

        return {"message": "File parsed and embedded successfully", "index_id": index_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error parsing file: {str(e)}")


class QueryInput(BaseModel):
    Query: str
    Index_id: str


@app.post("/llamaparse/query")
async def query_pdf(query_input: QueryInput):
    try:
        print(f"Received query: {query_input.Query}, Index_id: {query_input.Index_id}")
        response = await llama_parser.query_pdf(query_input.Query, query_input.Index_id)
        return {"message": str(response)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error in query_pdf: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.post("/graphrag/global_search")
async def global_search(query_input: QueryInput):
    """global search"""
    try:
        print(f"Received query: {query_input.Query}, Index_id: {query_input.Index_id}")
        response = await run_global_search(query_input.Query, query_input.Index_id)
        return {"message": response}
    except Exception as e:
        print(f"Error in global_search: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/graphrag/local_search")
async def local_search(query_input: QueryInput):
    """Local search using GraphRAG"""
    try:
        print(f"Received query: {query_input.Query}, Index_id: {query_input.Index_id}")
        response = await run_local_search(query_input.Query, query_input.Index_id)
        return {"message": response}
    except Exception as e:
        print(f"Error in local_search: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/graphrag/indexing")
async def run_indexing(
    file: UploadFile = File(...),
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    try:
        # Create input directory if it doesn't exist
        input_dir = os.path.join("graphrag_rag", "input")
        os.makedirs(input_dir, exist_ok=True)

        # Save uploaded file to input directory
        file_path = os.path.join(input_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Verify file exists and wait a moment to ensure it's fully written
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Failed to save the file")

        await asyncio.sleep(1)  # Short delay to ensure file is fully written

        # Command to be executed
        command = ["python", "-m", "graphrag.index", "--root", "./graphrag_rag"]

        # Running the command
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        log_data = result.stdout
        pattern = r"output/\d{8}-\d{6}"
        match = re.search(pattern, log_data)

        extracted_path = None
        if match:
            extracted_path = match.group()
            print("Extracted Path:", extracted_path)
        else:
            print("No matching pattern found.")

        new_document = IndexedDocument(
            user_id=user_id,
            document_name=file.filename,
            index_id=extracted_path,
            indexing_method="GraphRAG"
        )

        db.add(new_document)
        db.commit()

        return {
            "message": "Indexing completed successfully",
            "details": result.stdout,
            "extracted_path": extracted_path
        }

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        # Delete the file after processing
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not authenticate_user(user, form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user_id=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/register")
async def register(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == form_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        hashed_password = get_password_hash(form_data.password)
        new_user = User(email=form_data.username, password=hashed_password)
        db.add(new_user)
        db.commit()

        # Generate access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            user_id=new_user.id, expires_delta=access_token_expires
        )

        return {"message": "User registered successfully", "access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/indexed-documents")
async def get_indexed_documents(db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    documents = db.query(IndexedDocument).filter(IndexedDocument.user_id == user_id).all()
    return [{
        "id": doc.id,
        "document_name": doc.document_name,
        "indexing_method": doc.indexing_method,
        "index_id": doc.index_id  # Make sure this line is included
    } for doc in documents]


# Serve static files
app.mount("/static", StaticFiles(directory="/Users/linussoderberg/chatbot/server/multimodal_rag/output_images"), name="static")


@app.get("/pdf-images/{index_id}")
async def get_pdf_images(index_id: str):
    image_dir = Path(f"llamaparse_rag/storage/{index_id}/images")
    if not image_dir.exists():
        raise HTTPException(status_code=404, detail="Images not found")

    image_urls = [f"/static/{index_id}/images/{img.name}" for img in image_dir.glob("*.png")]
    return image_urls


import uuid
from datetime import datetime

@app.post("/multimodal_rag/upload_pdf")
async def multimodal_upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    try:
        upload_dir = "/Users/linussoderberg/chatbot/server/multimodal_rag/uploaded_pdfs"
        os.makedirs(upload_dir, exist_ok=True)

        # Generate a unique index_id
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]  # Use first 8 characters of a UUID
        index_id = f"{timestamp}_{unique_id}"

        file_path = os.path.join(upload_dir, f"{index_id}_{file.filename}")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Define the output folder for images
        output_folder = f"/Users/linussoderberg/chatbot/server/multimodal_rag/output_images/{index_id}"
        os.makedirs(output_folder, exist_ok=True)

        # Convert the uploaded PDF to images and place them in the output folder
        pdf_to_images(pdf_path=file_path, output_folder=output_folder, width=800)
        print("pdf_to_images done")
        output_directory = "/Users/linussoderberg/chatbot/server/multimodal_rag/output_directory/all_responses.json"
        print("before analyzer")
        analyzer = ClaudeImageAnalyzer(image_directory=output_folder, output_file_path=output_directory)
        analyzer.analyze_images()
        print("analyze_image done")
        # Create FAISS index
        faiss_save_directory = f'/Users/linussoderberg/chatbot/server/multimodal_rag/faiss_index/{index_id}'
        faiss_index_name = 'faiss_index'
        embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
        print("before process_json_files")
        output_directory_2 = "/Users/linussoderberg/chatbot/server/multimodal_rag/output_directory"
        library = process_json_files(directory_path=output_directory_2)
        print("after process_json_files")
        save_faiss_index(library, faiss_save_directory, faiss_index_name)

        # Verify that the index was saved
        full_index_path = os.path.join(faiss_save_directory, faiss_index_name)
        if not os.path.exists(full_index_path):
            print(f"Warning: FAISS index file not found at {full_index_path}")
            print(f"Contents of {faiss_save_directory}:")
            for item in os.listdir(faiss_save_directory):
                item_path = os.path.join(faiss_save_directory, item)
                print(f"  - {item} ({os.path.getsize(item_path)} bytes)")
            
            # Check if the file exists with a .faiss extension
            if os.path.exists(full_index_path + '.faiss'):
                print(f"Found FAISS index file with .faiss extension")
                full_index_path += '.faiss'
            else:
                raise Exception(f"FAISS index file was not created at {full_index_path}")

        print(f"FAISS index saved successfully at {full_index_path}")
        print(f"File size: {os.path.getsize(full_index_path)} bytes")

        # Save document information to the database
        new_document = IndexedDocument(
            user_id=user_id,
            document_name=file.filename,
            index_id=index_id,  # Using the new unique index_id
            indexing_method="vision-pdf-rag"
        )
        db.add(new_document)
        db.commit()

        return {"message": "File uploaded, processed, and indexed successfully", "index_id": index_id}
    except Exception as e:
        print(f"Error in multimodal_upload_pdf: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload and process file: {str(e)}")


class VectorDBQuery(BaseModel):
    query: str
    index_id: str
    top_k: int = 5

@app.post("/create_index")
async def create_index():
    try:
        faiss_save_directory = '/Users/linussoderberg/chatbot/server/multimodal_rag/faiss_index'
        faiss_index_name = 'faiss_index'
        embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")

        output_directory = '/Users/linussoderberg/chatbot/server/multimodal_rag/output_directory'
        library = process_json_files(output_directory)
        save_faiss_index(library, faiss_save_directory, faiss_index_name)
        app.state.library = library
        return {"message": "FAISS index created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating FAISS index: {str(e)}")

@app.post("/multimodal_rag/query_vector_db")
async def vector_db_query(
    query_input: VectorDBQuery,
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
    token: str = Depends(oauth2_scheme)
):
    try:
        # Verify that the index belongs to the user
        document = db.query(IndexedDocument).filter(
            IndexedDocument.index_id == query_input.index_id,
            IndexedDocument.user_id == user_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Index not found or not authorized")

        # Load the correct FAISS index
        faiss_save_directory = f'/Users/linussoderberg/chatbot/server/multimodal_rag/faiss_index/{query_input.index_id}'
        faiss_index_name = 'faiss_index'
        embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
        
        print(f"Attempting to load FAISS index for index_id: {query_input.index_id}")
        print(f"FAISS save directory: {faiss_save_directory}")
        print(f"FAISS index name: {faiss_index_name}")
        
        if not os.path.exists(faiss_save_directory):
            print(f"Directory does not exist: {faiss_save_directory}")
            raise FileNotFoundError(f"FAISS index directory not found: {faiss_save_directory}")
        
        print(f"Contents of {faiss_save_directory}:")
        for item in os.listdir(faiss_save_directory):
            print(f"  - {item}")
        
        library = load_faiss_index(faiss_save_directory, faiss_index_name, embeddings_model)
        
        # Retrieve Initial Vector DB Results
        results = query_vector_db(query_input.query, library, top_k=query_input.top_k)
        if not results:
            return {"results": [], "selected_page": None}
        
        # Format the results
        formatted_results = [{
            "page_content": doc.page_content,
            "metadata": doc.metadata
        } for doc in results]
        
        # Use Claude to Re-Rank and Select the Most Relevant Page
        selected_page_number = get_claude_recommendation(query_input.query, formatted_results)
        
        return {
            "results": formatted_results,
            "selected_page": selected_page_number
        }
    
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {str(e)}")
        raise HTTPException(status_code=404, detail=f"FAISS index not found: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error querying vector database: {str(e)}")

# Mount the static files directory
app.mount("/static", StaticFiles(directory="/Users/linussoderberg/chatbot/server/multimodal_rag/output_images"), name="static")

import re

@app.get("/multimodal_rag/get_image_paths/{index_id}")
async def get_image_paths(index_id: str, request: Request):
    image_directory = f"/Users/linussoderberg/chatbot/server/multimodal_rag/output_images/{index_id}"
    print(f"Searching for images in directory: {image_directory}")
    
    if not os.path.exists(image_directory):
        print(f"Directory not found: {image_directory}")
        raise HTTPException(status_code=404, detail=f"Image directory not found for index_id: {index_id}")
    
    def sort_key(filename):
        # Extract the number from the filename
        match = re.search(r'page_(\d+)', filename)
        if match:
            return int(match.group(1))
        return 0  # Default to 0 if no number found

    image_files = sorted([f for f in os.listdir(image_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))], key=sort_key)
    print(f"Found {len(image_files)} image files")
    
    if not image_files:
        print("No image files found in the directory")
        return {"image_paths": []}
    
    base_url = str(request.base_url)
    image_paths = [f"{base_url}static/{index_id}/{file}" for file in image_files]
    print(f"Returning {len(image_paths)} image paths")
    return {"image_paths": image_paths}