import numpy as np

def top1_reranker(results):
    """
    Filter results to only return the top 1 item based on similarity score.
    
    Args:
        results: List of content items with similarity scores
        
    Returns:
        List containing only the single highest-scoring content item, or empty list if no results
    """
    if not results:
        return []
    
    # Sort results by similarity in descending order
    sorted_results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)
    
    # Return only the top result
    return [sorted_results[0]]


def top3_reranker(results):
    """
    Filter results to return the top 3 items based on similarity score.
    
    Args:
        results: List of content items with similarity scores
        
    Returns:
        List containing up to 3 highest-scoring content items, sorted by similarity
    """
    if not results:
        return []
    
    # Sort results by similarity in descending order
    sorted_results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)
    
    # Return up to 3 results
    return sorted_results[:min(3, len(sorted_results))]


def uprank_sdr_reranker(results):
    """
    Filter results to return the top item, but boost items with 'SDR' tag by 20%.
    The boost is smoothed to asymptote to 1.0 for very high similarity scores.
    
    Args:
        results: List of content items with similarity scores
        
    Returns:
        List containing the single highest-scoring content item after boosting
    """
    if not results:
        return []
    
    # Create a copy of results to avoid modifying the original
    boosted_results = []
    
    for item in results:
        # Create a copy of the item
        boosted_item = item.copy()
        similarity = item.get('similarity', 0)
        
        # Check if item has 'SDR' tag
        tags = item.get('tags', [])
        if 'SDR' in tags:
            # Apply smoothed 20% boost that asymptotes to 1.0
            # Formula: new_sim = sim + boost * (1 - sim)
            # This ensures the similarity never exceeds 1.0
            boost_factor = 0.2
            boosted_similarity = similarity + (boost_factor * (1 - similarity))
            boosted_item['similarity'] = boosted_similarity
            boosted_item['boosted'] = True  # Optional flag to indicate boosting was applied
        
        boosted_results.append(boosted_item)
    
    # Sort boosted results by similarity in descending order
    sorted_results = sorted(boosted_results, key=lambda x: x.get('similarity', 0), reverse=True)
    
    # Return only the top result after boosting
    return [sorted_results[0]]