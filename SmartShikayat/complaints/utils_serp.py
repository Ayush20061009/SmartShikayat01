from serpapi import GoogleSearch
from django.conf import settings

def search_google_maps(query):
    """
    Searches Google Maps via SerpApi for a given query.
    Returns a list of dicts with 'address' and 'title'.
    """
    params = {
        "engine": "google_maps",
        "q": query,
        "api_key": settings.SERPAPI_KEY,
        "type": "search",
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Parse results
        places = []
        if "local_results" in results:
            for result in results["local_results"]:
                places.append({
                    "title": result.get("title"),
                    "address": result.get("address"),
                    "gps_coordinates": result.get("gps_coordinates") 
                })
        return places
    except Exception as e:
        print(f"SerpApi Error: {e}")
        return []
