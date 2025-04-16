# Import the necessary libraries
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import pickle
import json

# Import FAISS (CPU version for notebook testing)
try:
    import faiss
except ImportError:
    # If FAISS is not installed, print a message
    print("FAISS not installed. Please run: pip install faiss-cpu")
    
# Import SentenceTransformer
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    # If SentenceTransformer is not installed, print a message
    print("SentenceTransformer not installed. Please run: pip install sentence-transformers")

# Define a class for content indexing and retrieval
class ContentIndexer:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the ContentIndexer with a sentence transformer model.
        
        Args:
            model_name: The name of the sentence transformer model to use
        """
        self.model = SentenceTransformer(model_name)

        # Set absolute paths directly
        self.index_store_path = "C:/Users/dusan/OneDrive/Desktop/pp/plannerv2/config/faiss_indexes"
        self.content_store_path = "C:/Users/dusan/OneDrive/Desktop/pp/plannerv2/config/faiss_content"
        
        # Print paths for debugging
        print(f"Using index store path: {self.index_store_path}")
        print(f"Using content store path: {self.content_store_path}")
        
        # Create directories if they don't exist
        os.makedirs(self.index_store_path, exist_ok=True)
        os.makedirs(self.content_store_path, exist_ok=True)
    
    def _encode_text(self, text: str) -> np.ndarray:
        """
        Encode text into a vector using the sentence transformer model.
        
        Args:
            text: The text to encode
            
        Returns:
            A numpy array with the encoded vector
        """
        return self.model.encode(text)
    
    def create_or_update_index(self, index_name: str, content_items: List[Dict[str, Any]]) -> None:
        """
        Create or update a FAISS index for the given content items.
        
        Args:
            index_name: The name of the index to create or update
            content_items: List of content items, each should have at least 'title', 'body', and 'query_strings'
        """
        print(f"Creating/updating index '{index_name}' with {len(content_items)} items")
        
        # Filter content items for this index
        filtered_items = [item for item in content_items if item.get('index_name') == index_name]
        
        if not filtered_items:
            print(f"No content items found for index '{index_name}'")
            return
        
        # Create vectors for all content items and their query strings
        vectors = []
        content_mapping = []
        
        for idx, item in enumerate(filtered_items):
            # Create a vector for the title and body together
            title = item.get('title', '')
            body = item.get('body', '')
            main_text = f"{title} {body}"
            main_vector = self._encode_text(main_text)
            vectors.append(main_vector)
            content_mapping.append({
                'content_idx': idx,
                'query_idx': None  # This is the main content vector
            })
            
            # Create vectors for all query strings
            query_strings = item.get('query_strings', [])
            for q_idx, query in enumerate(query_strings):
                query_vector = self._encode_text(query)
                vectors.append(query_vector)
                content_mapping.append({
                    'content_idx': idx,
                    'query_idx': q_idx
                })
        
        # Convert to numpy array
        vectors_array = np.array(vectors).astype('float32')
        
        # Create FAISS index
        dimension = vectors_array.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(vectors_array)
        
        # Save the index
        index_path = os.path.join(self.index_store_path, f"{index_name}.index")
        faiss.write_index(index, index_path)
        
        # Save the content items and mapping
        content_path = os.path.join(self.content_store_path, f"{index_name}.pkl")
        with open(content_path, 'wb') as f:
            pickle.dump({
                'content_items': filtered_items,
                'content_mapping': content_mapping
            }, f)
        
        print(f"Index created successfully with {len(vectors)} vectors (including query strings)")

    def retrieve_content(self, 
                        index_name: str, 
                        query: str, 
                        top_k: int = 5, 
                        similarity_threshold: float = 0.0,
                        user_fields: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve content from a FAISS index based on a query and filter by user fields.
        
        Args:
            index_name: The name of the index to search
            query: The query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1) for inclusion in results
            user_fields: Optional dictionary of user fields to filter on (e.g. {"region2": "US"})
            
        Returns:
            List of content items with their similarity scores
        """
        # Check if index exists
        index_path = os.path.join(self.index_store_path, f"{index_name}.index")
        content_path = os.path.join(self.content_store_path, f"{index_name}.pkl")
        
        if not os.path.exists(index_path) or not os.path.exists(content_path):
            print(f"Index '{index_name}' not found")
            return []
        
        # Load the index
        index = faiss.read_index(index_path)
        
        # Load the content items and mapping
        with open(content_path, 'rb') as f:
            data = pickle.load(f)
            content_items = data['content_items']
            content_mapping = data['content_mapping']
        
        # Encode the query
        query_vector = self._encode_text(query).reshape(1, -1).astype('float32')
        
        # Get more results initially if we're filtering to ensure we still have enough after filtering
        search_k = top_k * 3 if user_fields else top_k
        
        # Search the index
        distances, indices = index.search(query_vector, search_k)
        
        # Process the results
        results = []
        seen_content_indices = set()
        
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= len(content_mapping):
                continue
            
            # Calculate similarity score (convert distance to similarity)
            # FAISS L2 distance - smaller is better, so we invert the scaling
            max_distance = 100  # Arbitrary large value
            similarity = max(0, 1 - (dist / max_distance))
            
            if similarity < similarity_threshold:
                continue
            
            # Get the content item index
            content_idx = content_mapping[idx]['content_idx']
            
            # Skip if we've already seen this content item
            if content_idx in seen_content_indices:
                continue
            
            # Add to results
            content_item = content_items[content_idx].copy()
            
            # Apply user field filtering if provided
            if user_fields and not self._matches_user_fields(content_item, user_fields):
                continue
                
            seen_content_indices.add(content_idx)
            content_item['similarity'] = similarity
            results.append(content_item)
            
            # Stop once we have enough results after filtering
            if len(results) >= top_k:
                break
        
        return results

    def _matches_user_fields(self, content_item: Dict[str, Any], user_fields: Dict[str, Any]) -> bool:
        """
        Check if a content item matches the given user fields.
        
        Args:
            content_item: The content item to check
            user_fields: The user fields to match against
            
        Returns:
            True if the content item matches all user fields, False otherwise
        """
        # Parse user_fields_mapping from the content item
        try:
            content_fields = content_item.get('user_fields_mapping', {})
            if isinstance(content_fields, str):
                content_fields = json.loads(content_fields)
        except (json.JSONDecodeError, TypeError):
            content_fields = {}
        
        # If user_fields is provided but content has no field mapping, no match
        if user_fields and not content_fields:
            return False
        
        # Check each user field
        for field_name, field_value in user_fields.items():
            # If the field doesn't exist in the content item's mapping, it doesn't match
            if field_name not in content_fields:
                return False
            
            content_field_value = content_fields[field_name]
            
            # Handle list of values in content
            if isinstance(content_field_value, list):
                # If the content has a list of values, check if user value is in the list
                if str(field_value) not in [str(v) for v in content_field_value]:
                    return False
            # Handle single value comparison
            elif str(content_field_value) != str(field_value):
                return False
        
        return True
        

def build_all_indexes(content_config: Dict[str, Any], indexer: Optional[ContentIndexer] = None) -> None:
    """
    Build indexes for all unique index_name values in the content configuration.
    
    Args:
        content_config: The content configuration dictionary with 'items' list
        indexer: Optional ContentIndexer instance (will create one if not provided)
    """
    if indexer is None:
        indexer = ContentIndexer()
    
    # Get all unique index names
    items = content_config.get('items', [])
    index_names = set(item.get('index_name') for item in items if 'index_name' in item)
    
    # Build each index
    for index_name in index_names:
        indexer.create_or_update_index(index_name, items)
    
    print(f"Built {len(index_names)} indexes: {', '.join(index_names)}")


def retrieve_filtered_content(
    index_name: str, 
    query: str, 
    user_fields: dict = None, 
    top_k: int = 5, 
    similarity_threshold: float = 0.0,
    model_name: str = "all-MiniLM-L6-v2"
):
    """
    Retrieve content from a specified index based on a query and filter by user fields.
    
    Args:
        index_name: The name of the index to search
        query: The query text to search for
        user_fields: Dictionary of user fields to filter on (e.g. {"region32": "US", "age": "12"})
        top_k: Number of results to return
        similarity_threshold: Minimum similarity score (0-1) for inclusion in results
        model_name: The sentence transformer model to use
        
    Returns:
        List of content items with their similarity scores
    """
    # Initialize the indexer with the specified model
    indexer = ContentIndexer(model_name)
    
    # Call the retrieve_content method
    results = indexer.retrieve_content(
        index_name=index_name,
        query=query,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
        user_fields=user_fields
    )
    
    return results


def diagnose_retrieval_system():
    """Diagnose the retrieval system configuration and file access."""
    import os
    import pickle
    
    # Check working directory
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    # Check if index directories exist and are accessible
    index_dir = os.path.join(cwd, "config", "faiss_indexes")
    content_dir = os.path.join(cwd, "config", "faiss_content")
    
    print(f"Index directory: {index_dir}")
    print(f"  - Exists: {os.path.exists(index_dir)}")
    print(f"  - Is directory: {os.path.isdir(index_dir) if os.path.exists(index_dir) else 'N/A'}")
    print(f"  - Readable: {os.access(index_dir, os.R_OK) if os.path.exists(index_dir) else 'N/A'}")
    print(f"  - Writable: {os.access(index_dir, os.W_OK) if os.path.exists(index_dir) else 'N/A'}")
    
    print(f"Content directory: {content_dir}")
    print(f"  - Exists: {os.path.exists(content_dir)}")
    print(f"  - Is directory: {os.path.isdir(content_dir) if os.path.exists(content_dir) else 'N/A'}")
    print(f"  - Readable: {os.access(content_dir, os.R_OK) if os.path.exists(content_dir) else 'N/A'}")
    print(f"  - Writable: {os.access(content_dir, os.W_OK) if os.path.exists(content_dir) else 'N/A'}")
    
    # List all indexes
    if os.path.exists(index_dir):
        index_files = [f for f in os.listdir(index_dir) if f.endswith(".index")]
        print(f"Index files: {index_files}")
        
        # Check each index file
        for idx_file in index_files:
            idx_path = os.path.join(index_dir, idx_file)
            content_path = os.path.join(content_dir, idx_file.replace(".index", ".pkl"))
            index_name = idx_file.replace(".index", "")
            
            print(f"Index: {idx_file}")
            print(f"  - Size: {os.path.getsize(idx_path)} bytes")
            print(f"  - Modified: {os.path.getmtime(idx_path)}")
            print(f"  - Readable: {os.access(idx_path, os.R_OK)}")
            
            if os.path.exists(content_path):
                print(f"  - Content file exists: Yes")
                print(f"  - Content size: {os.path.getsize(content_path)} bytes")
                print(f"  - Content modified: {os.path.getmtime(content_path)}")
                
                # Try to load content file and count content items
                try:
                    with open(content_path, 'rb') as f:
                        data = pickle.load(f)
                        content_items = data.get('content_items', [])
                        content_mapping = data.get('content_mapping', [])
                        
                        print(f"  - Content items count: {len(content_items)}")
                        print(f"  - Content mapping count: {len(content_mapping)}")
                        
                        # Print titles of content items
                        print(f"  - Content titles:")
                        for item in content_items:
                            title = item.get('title', 'Untitled')
                            print(f"    - {title}")
                except Exception as e:
                    print(f"  - Error loading content file: {str(e)}")
            else:
                print(f"  - Content file exists: No")
    
    # Also check content.json file
    content_json_path = os.path.join(cwd, "config", "content.json")
    if os.path.exists(content_json_path):
        print("\nContent JSON file:")
        print(f"  - Path: {content_json_path}")
        print(f"  - Size: {os.path.getsize(content_json_path)} bytes")
        print(f"  - Modified: {os.path.getmtime(content_json_path)}")
        print(f"  - Readable: {os.access(content_json_path, os.R_OK)}")
        
        try:
            import json
            with open(content_json_path, 'r') as f:
                content_data = json.load(f)
                items = content_data.get('items', [])
                print(f"  - Total items in content.json: {len(items)}")
                
                # Group by index name
                indexes = {}
                for item in items:
                    idx = item.get('index_name', '')
                    if idx not in indexes:
                        indexes[idx] = []
                    indexes[idx].append(item)
                
                print(f"  - Items by index:")
                for idx, items in indexes.items():
                    idx_name = idx if idx else '(no index)'
                    print(f"    - {idx_name}: {len(items)} items")
        except Exception as e:
            print(f"  - Error loading content.json: {str(e)}")
    else:
        print("\nContent JSON file does not exist")
    
    return "Diagnosis complete"