"""Vector Memory using ChromaDB for semantic search."""
import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class VectorMemory:
    """Manages vector embeddings for semantic memory."""
    
    def __init__(self, db_path: str = "./data/chroma", collection_name: str = "invoices_unstructured"):
        """Initialize ChromaDB with persistent storage using new API."""
        # Create directory if it doesn't exist
        db_dir = Path(db_path)
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Use new PersistentClient API (ChromaDB v0.4+)
        self.client = chromadb.PersistentClient(path=str(db_dir))
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Invoice transaction semantic memory"}
        )

        self.compliance_rules_collection = self.client.get_or_create_collection(
            name="compliance_rules",
            metadata={"description": "Country-specific compliance rules and laws"}
        )

    def add_compliance_rule(
        self,
        country_code: str,
        rule_text: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Store compliance rules for semantic retrieval."""
        self.compliance_rules_collection.add(
            documents=[rule_text],
            metadatas=[{
                **metadata,
                "country_code": country_code,
                "timestamp": datetime.utcnow().isoformat()
            }],
            ids=[f"rule_{country_code}_{datetime.utcnow().timestamp()}"]
        )

    def search_compliance_rules(
        self,
        query: str,
        country_code: Optional[str] = None,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for relevant compliance rules."""
        where_filter = {"country_code": country_code} if country_code else None

        results = self.compliance_rules_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )

        return self._format_results(results)
    
    def add_transaction_context(
        self,
        transaction_id: str,
        context: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Store transaction context with semantic embeddings."""
        self.collection.add(
            documents=[context],
            metadatas=[{
                **metadata,
                "transaction_id": transaction_id,
                "timestamp": datetime.utcnow().isoformat()
            }],
            ids=[f"txn_{transaction_id}_{datetime.utcnow().timestamp()}"]
        )
    
    def add_communication_context(
        self,
        communication_id: str,
        message: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Store communication history for relationship context."""
        self.collection.add(
            documents=[message],
            metadatas=[{
                **metadata,
                "communication_id": communication_id,
                "timestamp": datetime.utcnow().isoformat()
            }],
            ids=[f"comm_{communication_id}_{datetime.utcnow().timestamp()}"]
        )
    
    def search_similar_transactions(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar transaction contexts."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_metadata
        )
        
        return self._format_results(results)
    
    def get_customer_history(
        self,
        customer_id: str,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve semantic history for a customer."""
        results = self.collection.query(
            query_texts=["customer payment history and relationship context"],
            n_results=n_results,
            where={"customer_id": customer_id}
        )
        
        return self._format_results(results)
    
    def _format_results(self, results: Dict) -> List[Dict[str, Any]]:
        """Format ChromaDB results."""
        formatted = []
        for i in range(len(results['ids'][0])):
            formatted.append({
                "id": results['ids'][0][i],
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })
        return formatted
