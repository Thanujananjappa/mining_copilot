import os
import sys
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from config import Config
import logging

logger = logging.getLogger(__name__)

class LangChainSetup:
    def __init__(self):
        """Initialize LangChain components"""
        self.embeddings = None
        self.vector_store = None
        self.qa_chain = None
        self.initialize_components()
    
    def initialize_components(self):
        """Initialize all LangChain components"""
        try:
            from sentence_transformers import SentenceTransformer
            # Load model directly without HuggingFaceEmbeddings wrapper
            model = SentenceTransformer(Config.EMBEDDING_MODEL)
            
            # Create a simple wrapper
            class SimpleEmbeddings:
                def __init__(self, model):
                    self.model = model
                def embed_documents(self, texts):
                    return self.model.encode(texts).tolist()
                def embed_query(self, text):
                    return self.model.encode([text])[0].tolist()
            
            self.embeddings = SimpleEmbeddings(model)
            logger.info("✅ Embeddings initialized successfully")
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Failed to initialize embeddings: {e}")
            logger.error(traceback.format_exc())
    
    def create_custom_prompt(self):
        """Create custom prompt template for mining domain"""
        
        prompt_template = """You are an expert mining and infrastructure management assistant. 
Use the following context to provide a concise, actionable answer in 3-4 sentences maximum.

Context: {context}

Question: {question}

Guidelines:
- Focus on key insights for mine managers
- Be specific and actionable
- Highlight safety concerns if any
- Mention efficiency and productivity impacts
- Keep it concise (3-4 sentences)

Concise Answer:"""

        return PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
    
    def create_text_splitter(self):
        """Create text splitter for document processing"""
        return RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def create_documents_from_texts(self, texts, metadatas=None):
        """Create LangChain documents from text list"""
        documents = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            doc = Document(page_content=text, metadata=metadata)
            documents.append(doc)
        return documents
    
    def get_embedding_model_info(self):
        """Get information about the embedding model"""
        if self.embeddings:
            return {
                "model_name": Config.EMBEDDING_MODEL,
                "embedding_size": 384
            }
        return {"error": "Embeddings not initialized"}

# Global instance
langchain_setup = LangChainSetup()