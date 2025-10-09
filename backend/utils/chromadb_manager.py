import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from config import Config
import logging
import pandas as pd
import os

logger = logging.getLogger(__name__)

class ChromaDBManager:
    def __init__(self, embeddings=None):
        """Initialize ChromaDB manager with LOCAL storage"""
        try:
            # ✅ Initialize embeddings first (HuggingFace)
            if embeddings is None:
                self.embeddings = HuggingFaceEmbeddings(
                    model_name=Config.EMBEDDING_MODEL,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': False}
                )
            else:
                self.embeddings = embeddings
            
            # ✅ Use LOCAL persistent storage instead of server
            self.client = chromadb.PersistentClient(
                path="./chroma_data"  # Local directory to store data
            )
            
            self.collection_name = "mining_knowledge_base"
            
            # ✅ Create or get collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Mining Knowledge Base"}
            )

            logger.info(f"✅ Connected to ChromaDB (Local): {self.collection_name}")
        
        except Exception as e:
            logger.error(f"❌ ChromaDB initialization failed: {e}")
            # Fallback: try ephemeral client (in-memory)
            try:
                self.client = chromadb.EphemeralClient()
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "Mining Knowledge Base"}
                )
                logger.info(f"✅ Connected to ChromaDB (In-Memory): {self.collection_name}")
            except Exception as e2:
                logger.error(f"❌ ChromaDB fallback also failed: {e2}")
                self.client = None
                self.collection = None
                self.embeddings = None
    
    def add_documents(self, documents):
        """Add documents to ChromaDB with embeddings"""
        if not self.client or not self.collection:
            logger.error("ChromaDB not initialized")
            return False
        
        try:
            # Split large documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            chunks = text_splitter.split_documents(documents)
            
            # Add to ChromaDB with automatic embedding
            vectorstore = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
            
            vectorstore.add_documents(chunks)
            logger.info(f"✅ Added {len(chunks)} document chunks to ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents: {e}")
            return False
    
    def add_csv_data(self, csv_file_path, document_type):
        """Load data from CSV files and add to ChromaDB"""
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            
            documents = []
            # Convert each row to a document
            for idx, row in df.iterrows():
                # Create meaningful text content from the row
                content = self._row_to_text(row, document_type)
                
                # Create document with metadata
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": os.path.basename(csv_file_path),
                        "type": document_type,
                        "row_id": idx
                    }
                )
                documents.append(doc)
            
            # Add to ChromaDB
            if documents:
                success = self.add_documents(documents)
                if success:
                    logger.info(f"✅ Added {len(documents)} documents from {csv_file_path}")
                    return True
                else:
                    return False
            else:
                logger.warning(f"⚠️ No documents created from {csv_file_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to load CSV {csv_file_path}: {e}")
            return False
    
    def _row_to_text(self, row, doc_type):
        """Convert CSV row to meaningful text content"""
        if doc_type == "equipment":
            return f"""
            Equipment Monitoring:
            ID: {row.get('equipment_id', 'N/A')}
            Type: {row.get('equipment_type', 'N/A')}
            Status: {row.get('status', 'N/A')}
            Efficiency: {row.get('efficiency_score', 'N/A')}%
            Alerts: {row.get('alerts', 'None')}
            Last Maintenance: {row.get('last_maintenance', 'N/A')}
            Temperature: {row.get('temperature_celsius', 'N/A')}°C
            Vibration: {row.get('vibration_level', 'N/A')}
            """
        
        elif doc_type == "incidents":
            return f"""
            Mining Incident:
            Date: {row.get('incident_date', 'N/A')}
            Mine: {row.get('mine_name', 'N/A')}
            Type: {row.get('incident_type', 'N/A')}
            Severity: {row.get('severity', 'N/A')}
            Description: {row.get('description', 'N/A')}
            Casualties: {row.get('casualties', 0)}
            Injuries: {row.get('injuries', 0)}
            Cost Impact: ${row.get('cost_impact', 0)}
            """
        
        elif doc_type == "production":
            return f"""
            Production Metrics:
            Date: {row.get('metric_date', 'N/A')}
            Site: {row.get('site_name', 'N/A')}
            Material: {row.get('material_type', 'N/A')}
            Quantity: {row.get('quantity_tons', 0)} tons
            Target: {row.get('target_tons', 0)} tons
            Efficiency: {row.get('efficiency_percentage', 0)}%
            Downtime: {row.get('downtime_hours', 0)} hours
            Cost per Ton: ${row.get('cost_per_ton', 0)}
            """
        
        elif doc_type == "safety":
            return f"""
            Safety Compliance:
            Audit Date: {row.get('audit_date', 'N/A')}
            Site: {row.get('site_name', 'N/A')}
            Compliance Score: {row.get('compliance_score', 0)}%
            Violations: {row.get('violations', 0)}
            Recommendations: {row.get('recommendations', 'None')}
            """
        
        elif doc_type == "maintenance":
            return f"""
            Maintenance Record:
            Equipment: {row.get('equipment_id', 'N/A')}
            Type: {row.get('maintenance_type', 'N/A')}
            Start: {row.get('start_date', 'N/A')}
            End: {row.get('end_date', 'N/A')}
            Cost: ${row.get('cost', 0)}
            Downtime: {row.get('downtime_hours', 0)} hours
            """
        
        elif doc_type == "fuel":
            return f"""
            Fuel & Energy:
            Equipment: {row.get('equipment_id', 'N/A')}
            Date: {row.get('reading_date', 'N/A')}
            Fuel: {row.get('fuel_liters', 0)} liters
            Energy: {row.get('energy_kwh', 0)} kWh
            Shift: {row.get('shift', 'N/A')}
            """
        
        elif doc_type == "quality":
            return f"""
            Quality Metrics:
            Site: {row.get('site_name', 'N/A')}
            Date: {row.get('metric_date', 'N/A')}
            Material: {row.get('material_type', 'N/A')}
            Grade: {row.get('quality_grade', 'N/A')}
            Defects: {row.get('defects_found', 0)}
            """
        
        else:
            # Generic fallback - convert all columns to text
            content_parts = [f"{col}: {row.get(col, 'N/A')}" for col in row.index]
            return "\n".join(content_parts)
    
    def similarity_search(self, query, k=5):
        """Perform semantic search with embeddings"""
        if not self.client or not self.collection:
            logger.warning("⚠️ ChromaDB not initialized, returning empty results")
            return []
        
        try:
            vectorstore = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
            return vectorstore.similarity_search(query, k=k)
        except Exception as e:
            logger.error(f"❌ Similarity search failed: {e}")
            return []
    
    def get_collection_info(self):
        """Get information about the collection"""
        if not self.collection:
            return "No collection available"
        
        try:
            count = self.collection.count()
            return f"Collection '{self.collection_name}' has {count} documents"
        except Exception as e:
            return f"Error getting collection info: {e}"