import os
import asyncio
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage
from dotenv import load_dotenv
import aiofiles.tempfile as tempfile
import uuid
from pathlib import Path
import logging


load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
llama_cloud_api_key = os.getenv('LLAMA_CLOUD_API_KEY')


class LlamaParser:

    def __init__(self):
        self.index = None
        self.index_id = None
        self.storage_dir = Path("/Users/linussoderberg/chatbot/server/storage")
        os.makedirs(self.storage_dir, exist_ok=True)  # Ensure the directory exists

    async def parse_pdf(self, file):
        """
        Parse the uploaded pdf file and return the documents.
        """
        self.index_id = str(uuid.uuid4())  # Generate index_id here
        
        parser = LlamaParse(
            result_type="markdown",
            num_workers=4,
            verbose=True,
            language="en",
        )

        async with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            content = await file.read()
            await temp_pdf.write(content)
            temp_pdf_path = temp_pdf.name

        try:
            file_extractor = {".pdf": parser}
            reader = SimpleDirectoryReader(
                input_files=[temp_pdf_path], file_extractor=file_extractor)
            documents = await reader.aload_data()
            # After parsing the PDF, log the location of the generated images
            image_dir = self.storage_dir / self.index_id / "images"
            logging.info(f"Generated PDF images are saved in: {image_dir}")
            logging.info(f"Number of images generated: {len(list(image_dir.glob('*.png')))}")
            return documents
        finally:
            os.unlink(temp_pdf_path)

    async def create_and_save_index(self, documents):
        """
        Create an index from the parsed documents and save it.
        """
        self.index = VectorStoreIndex.from_documents(documents)
        # self.index_id is already set in parse_pdf, so we don't need to generate it again

        index_id_path = self.storage_dir / self.index_id
        index_id_path.mkdir(parents=True, exist_ok=True)

        self.index.storage_context.persist(persist_dir=str(index_id_path))
        return self.index_id

    async def parse_and_embed_pdf(self, file):
        """
        Parse the uploaded pdf file, embed it, and save the index.
        """
        documents = await self.parse_pdf(file)
        return await self.create_and_save_index(documents)

    async def load_index(self, index_id):
        """
        Load a previously saved index
        """
        index_id_path = self.storage_dir / index_id
        if index_id_path.exists():
            storage_context = StorageContext.from_defaults(
                persist_dir=str(index_id_path))
            self.index = load_index_from_storage(storage_context)
            self.index_id = index_id
        else:
            raise ValueError(f"No saved index found for ID: {index_id}")

    async def query_pdf(self, query, index_id=None):
        """
        Query the embedded pdf
        """
        if index_id and self.index_id != index_id:
            await self.load_index(index_id)

        if self.index is None:
            raise ValueError(
                "No index loaded. Please parse a PDF or load an existing index.")

        query_engine = self.index.as_query_engine()
        response = await query_engine.aquery(query)
        return response
