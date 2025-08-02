"""
Visual Collector Module
Fetches royalty-free videos and images from Pexels API and other sources
"""

import os
import requests
from dotenv import load_dotenv
from typing import List, Dict, Optional
import logging
import time
import random

# Load environment variables
load_dotenv()

class VisualCollector:
    def __init__(self):
        self.pexels_api_key = os.getenv('PEXELS_API_KEY')
        if not self.pexels_api_key:
            raise ValueError("Pexels API key not found. Please set PEXELS_API_KEY in .env file")
        
        self.pexels_headers = {
            "Authorization": self.pexels_api_key
        }
        
        self.pexels_base_url = "https://api.pexels.com"
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Common search terms for movie-related content
        self.generic_video_terms = [
            "cinematic", "film", "movie theater", "dramatic lighting", 
            "storytelling", "narrative", "cinema", "dark atmosphere",
            "mystery", "suspense", "drama", "artistic", "abstract",
            "bokeh lights", "city lights", "rain", "night city"
        ]
    
    def search_videos(self, query: str, per_page: int = 15, page: int = 1) -> List[Dict]:
        """
        Search for videos on Pexels
        
        Args:
            query: Search query
            per_page: Number of videos per page (max 80)
            page: Page number
            
        Returns:
            List of video data
        """
        try:
            url = f"{self.pexels_base_url}/videos/search"
            params = {
                "query": query,
                "per_page": min(per_page, 80),
                "page": page,
                "orientation": "landscape",
                "size": "large"
            }
            
            response = requests.get(url, headers=self.pexels_headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = data.get('videos', [])
            
            self.logger.info(f"Found {len(videos)} videos for query: {query}")
            return videos
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching videos: {e}")
            return []
    
    def search_photos(self, query: str, per_page: int = 15, page: int = 1) -> List[Dict]:
        """
        Search for photos on Pexels
        
        Args:
            query: Search query
            per_page: Number of photos per page (max 80)
            page: Page number
            
        Returns:
            List of photo data
        """
        try:
            url = f"{self.pexels_base_url}/search"
            params = {
                "query": query,
                "per_page": min(per_page, 80),
                "page": page,
                "orientation": "landscape",
                "size": "large"
            }
            
            response = requests.get(url, headers=self.pexels_headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            photos = data.get('photos', [])
            
            self.logger.info(f"Found {len(photos)} photos for query: {query}")
            return photos
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching photos: {e}")
            return []
    
    def get_popular_videos(self, per_page: int = 15, page: int = 1) -> List[Dict]:
        """
        Get popular/curated videos from Pexels
        
        Args:
            per_page: Number of videos per page
            page: Page number
            
        Returns:
            List of popular videos
        """
        try:
            url = f"{self.pexels_base_url}/videos/popular"
            params = {
                "per_page": min(per_page, 80),
                "page": page
            }
            
            response = requests.get(url, headers=self.pexels_headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = data.get('videos', [])
            
            self.logger.info(f"Retrieved {len(videos)} popular videos")
            return videos
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting popular videos: {e}")
            return []
    
    def download_media(self, url: str, output_path: str) -> Optional[str]:
        """
        Download media file from URL
        
        Args:
            url: Media URL
            output_path: Local path to save the file
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Downloaded media to: {output_path}")
            return output_path
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error downloading media: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error downloading media: {e}")
            return None
    
    def collect_movie_visuals(self, movie_data: Dict, output_dir: str = "./temp/visuals") -> Dict:
        """
        Collect relevant visuals based on movie data
        
        Args:
            movie_data: Movie information from TMDb
            output_dir: Directory to save downloaded visuals
            
        Returns:
            Dictionary containing paths to collected visuals
        """
        try:
            title = movie_data.get('title', 'Unknown Movie')
            genres = [g.get('name', '').lower() for g in movie_data.get('genres', [])]
            overview = movie_data.get('overview', '')
            
            self.logger.info(f"Collecting visuals for movie: {title}")
            
            # Generate search queries based on movie data
            search_queries = []
            
            # Add genre-based queries
            for genre in genres:
                if genre in ['action', 'thriller', 'horror', 'mystery']:
                    search_queries.extend(['dark cityscape', 'dramatic lighting', 'suspense'])
                elif genre in ['romance', 'drama']:
                    search_queries.extend(['emotional', 'intimate lighting', 'sunset'])
                elif genre in ['science fiction', 'sci-fi']:
                    search_queries.extend(['futuristic', 'technology', 'space', 'neon lights'])
                elif genre in ['fantasy', 'adventure']:
                    search_queries.extend(['magical', 'epic landscape', 'mystical'])
                elif genre in ['comedy']:
                    search_queries.extend(['bright', 'colorful', 'happy'])
            
            # Add generic cinematic terms
            search_queries.extend(self.generic_video_terms[:5])
            
            # Remove duplicates and limit queries
            search_queries = list(set(search_queries))[:8]
            
            collected_visuals = {
                'videos': [],
                'images': [],
                'background_videos': [],
                'transition_videos': []
            }
            
            # Collect videos for each search query
            for query in search_queries:
                videos = self.search_videos(query, per_page=5)
                
                for video in videos[:2]:  # Take top 2 videos per query
                    try:
                        # Get the highest quality video file
                        video_files = video.get('video_files', [])
                        if not video_files:
                            continue
                        
                        # Sort by file size (larger = higher quality)
                        video_files.sort(key=lambda x: x.get('file_size', 0), reverse=True)
                        best_video = video_files[0]
                        
                        video_url = best_video.get('link', '')
                        if not video_url:
                            continue
                        
                        # Generate filename
                        video_id = video.get('id', random.randint(1000, 9999))
                        filename = f"video_{video_id}_{query.replace(' ', '_')}.mp4"
                        output_path = os.path.join(output_dir, 'videos', filename)
                        
                        # Download video
                        downloaded_path = self.download_media(video_url, output_path)
                        if downloaded_path:
                            collected_visuals['videos'].append({
                                'path': downloaded_path,
                                'query': query,
                                'duration': video.get('duration', 0),
                                'width': best_video.get('width', 0),
                                'height': best_video.get('height', 0)
                            })
                        
                        # Small delay to avoid rate limiting
                        time.sleep(0.5)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing video: {e}")
                        continue
            
            # Collect some generic background videos
            background_videos = self.search_videos("cinematic background", per_page=10)
            for video in background_videos[:3]:
                try:
                    video_files = video.get('video_files', [])
                    if video_files:
                        video_files.sort(key=lambda x: x.get('file_size', 0), reverse=True)
                        best_video = video_files[0]
                        video_url = best_video.get('link', '')
                        
                        if video_url:
                            video_id = video.get('id', random.randint(1000, 9999))
                            filename = f"background_{video_id}.mp4"
                            output_path = os.path.join(output_dir, 'backgrounds', filename)
                            
                            downloaded_path = self.download_media(video_url, output_path)
                            if downloaded_path:
                                collected_visuals['background_videos'].append({
                                    'path': downloaded_path,
                                    'duration': video.get('duration', 0)
                                })
                            
                            time.sleep(0.5)
                            
                except Exception as e:
                    self.logger.error(f"Error processing background video: {e}")
                    continue
            
            # Collect some images for static shots or thumbnails
            image_queries = search_queries[:3]  # Use first 3 queries for images
            for query in image_queries:
                photos = self.search_photos(query, per_page=3)
                
                for photo in photos[:1]:  # Take 1 photo per query
                    try:
                        photo_url = photo.get('src', {}).get('large', '')
                        if not photo_url:
                            continue
                        
                        photo_id = photo.get('id', random.randint(1000, 9999))
                        filename = f"image_{photo_id}_{query.replace(' ', '_')}.jpg"
                        output_path = os.path.join(output_dir, 'images', filename)
                        
                        downloaded_path = self.download_media(photo_url, output_path)
                        if downloaded_path:
                            collected_visuals['images'].append({
                                'path': downloaded_path,
                                'query': query,
                                'width': photo.get('width', 0),
                                'height': photo.get('height', 0)
                            })
                        
                        time.sleep(0.5)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing image: {e}")
                        continue
            
            total_visuals = (len(collected_visuals['videos']) + 
                           len(collected_visuals['images']) + 
                           len(collected_visuals['background_videos']))
            
            self.logger.info(f"Collected {total_visuals} visual assets for {title}")
            return collected_visuals
            
        except Exception as e:
            self.logger.error(f"Error collecting movie visuals: {e}")
            return {'videos': [], 'images': [], 'background_videos': [], 'transition_videos': []}
    
    def get_transition_videos(self, count: int = 3, output_dir: str = "./temp/visuals") -> List[Dict]:
        """
        Get generic transition videos for video editing
        
        Args:
            count: Number of transition videos to collect
            output_dir: Output directory
            
        Returns:
            List of transition video information
        """
        try:
            transition_queries = [
                "black transition", "fade transition", "light leak", 
                "abstract transition", "bokeh transition"
            ]
            
            transition_videos = []
            
            for query in transition_queries[:count]:
                videos = self.search_videos(query, per_page=3)
                
                if videos:
                    video = videos[0]  # Take the first video
                    video_files = video.get('video_files', [])
                    
                    if video_files:
                        video_files.sort(key=lambda x: x.get('file_size', 0), reverse=True)
                        best_video = video_files[0]
                        video_url = best_video.get('link', '')
                        
                        if video_url:
                            video_id = video.get('id', random.randint(1000, 9999))
                            filename = f"transition_{video_id}.mp4"
                            output_path = os.path.join(output_dir, 'transitions', filename)
                            
                            downloaded_path = self.download_media(video_url, output_path)
                            if downloaded_path:
                                transition_videos.append({
                                    'path': downloaded_path,
                                    'query': query,
                                    'duration': video.get('duration', 0)
                                })
                            
                            time.sleep(0.5)
            
            self.logger.info(f"Collected {len(transition_videos)} transition videos")
            return transition_videos
            
        except Exception as e:
            self.logger.error(f"Error collecting transition videos: {e}")
            return []

def main():
    """Test the VisualCollector functionality"""
    try:
        collector = VisualCollector()
        
        # Test video search
        print("Searching for cinematic videos...")
        videos = collector.search_videos("cinematic", per_page=5)
        if videos:
            print(f"Found {len(videos)} videos")
            print(f"First video: {videos[0].get('id', 'Unknown')} - Duration: {videos[0].get('duration', 0)}s")
        
        # Test photo search
        print("\nSearching for dramatic photos...")
        photos = collector.search_photos("dramatic lighting", per_page=3)
        if photos:
            print(f"Found {len(photos)} photos")
            print(f"First photo: {photos[0].get('id', 'Unknown')} - {photos[0].get('width', 0)}x{photos[0].get('height', 0)}")
        
        # Test movie visual collection (sample movie data)
        sample_movie = {
            'title': 'Sample Movie',
            'genres': [{'name': 'Action'}, {'name': 'Thriller'}],
            'overview': 'A thrilling action movie with dramatic scenes.'
        }
        
        print(f"\nCollecting visuals for sample movie...")
        visuals = collector.collect_movie_visuals(sample_movie)
        print(f"Collected visuals:")
        print(f"- Videos: {len(visuals['videos'])}")
        print(f"- Images: {len(visuals['images'])}")
        print(f"- Background videos: {len(visuals['background_videos'])}")
        
    except Exception as e:
        print(f"Error running VisualCollector test: {e}")

if __name__ == "__main__":
    main() 