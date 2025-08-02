"""
Movie Scraper Module
Scrapes trending movies from TMDb API and provides movie details
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, List, Optional
import logging

# Load environment variables
load_dotenv()

class MovieScraper:
    def __init__(self):
        self.api_key = os.getenv('TMDB_API_KEY')
        if not self.api_key:
            raise ValueError("TMDb API key not found. Please set TMDB_API_KEY in .env file")
        
        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json"
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_trending_movies(self, time_window: str = "day", page: int = 1) -> List[Dict]:
        """
        Get trending movies from TMDb
        
        Args:
            time_window: 'day' or 'week'
            page: Page number (default: 1)
            
        Returns:
            List of trending movies
        """
        try:
            url = f"{self.base_url}/trending/movie/{time_window}"
            params = {"page": page}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            movies = data.get('results', [])
            
            self.logger.info(f"Retrieved {len(movies)} trending movies")
            return movies
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching trending movies: {e}")
            return []
    
    def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """
        Get detailed information about a specific movie
        
        Args:
            movie_id: TMDb movie ID
            
        Returns:
            Detailed movie information
        """
        try:
            url = f"{self.base_url}/movie/{movie_id}"
            params = {"append_to_response": "credits,videos,reviews,keywords"}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            movie_data = response.json()
            self.logger.info(f"Retrieved details for movie: {movie_data.get('title', 'Unknown')}")
            
            return movie_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching movie details for ID {movie_id}: {e}")
            return None
    
    def search_movies(self, query: str, page: int = 1) -> List[Dict]:
        """
        Search for movies by title
        
        Args:
            query: Search query
            page: Page number
            
        Returns:
            List of search results
        """
        try:
            url = f"{self.base_url}/search/movie"
            params = {
                "query": query,
                "page": page,
                "include_adult": False
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            movies = data.get('results', [])
            
            self.logger.info(f"Found {len(movies)} movies for query: {query}")
            return movies
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching movies: {e}")
            return []
    
    def get_popular_movies(self, page: int = 1) -> List[Dict]:
        """
        Get popular movies
        
        Args:
            page: Page number
            
        Returns:
            List of popular movies
        """
        try:
            url = f"{self.base_url}/movie/popular"
            params = {"page": page}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            movies = data.get('results', [])
            
            self.logger.info(f"Retrieved {len(movies)} popular movies")
            return movies
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching popular movies: {e}")
            return []
    
    def select_movie_for_breakdown(self) -> Optional[Dict]:
        """
        Select a suitable movie for breakdown based on trending and popularity
        
        Returns:
            Selected movie with full details
        """
        try:
            # Get trending movies first
            trending_movies = self.get_trending_movies()
            
            if not trending_movies:
                # Fallback to popular movies
                self.logger.info("No trending movies found, falling back to popular movies")
                trending_movies = self.get_popular_movies()
            
            if not trending_movies:
                self.logger.error("No movies found for breakdown")
                return None
            
            # Filter movies suitable for breakdown (recent releases, good ratings)
            suitable_movies = []
            for movie in trending_movies:
                # Check if movie has good rating and recent release
                if (movie.get('vote_average', 0) >= 6.0 and 
                    movie.get('release_date', '') >= '2020-01-01'):
                    suitable_movies.append(movie)
            
            if not suitable_movies:
                # If no suitable movies, take the first trending movie
                suitable_movies = trending_movies[:1]
            
            # Select the first suitable movie and get full details
            selected_movie = suitable_movies[0]
            movie_details = self.get_movie_details(selected_movie['id'])
            
            if movie_details:
                self.logger.info(f"Selected movie for breakdown: {movie_details.get('title')}")
                return movie_details
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error selecting movie for breakdown: {e}")
            return None

def main():
    """Test the MovieScraper functionality"""
    try:
        scraper = MovieScraper()
        
        # Test trending movies
        print("Fetching trending movies...")
        trending = scraper.get_trending_movies()
        if trending:
            print(f"Found {len(trending)} trending movies")
            print(f"First movie: {trending[0].get('title')}")
        
        # Test movie selection
        print("\nSelecting movie for breakdown...")
        selected_movie = scraper.select_movie_for_breakdown()
        if selected_movie:
            print(f"Selected: {selected_movie.get('title')}")
            print(f"Release Date: {selected_movie.get('release_date')}")
            print(f"Rating: {selected_movie.get('vote_average')}/10")
            print(f"Overview: {selected_movie.get('overview', '')[:100]}...")
        
    except Exception as e:
        print(f"Error running MovieScraper test: {e}")

if __name__ == "__main__":
    main() 