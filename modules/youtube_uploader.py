"""
YouTube Uploader Module
Uploads videos to YouTube using YouTube Data API v3
"""

import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from typing import Dict, Optional
import logging
import time
import random

# Load environment variables
load_dotenv()

class YouTubeUploader:
    def __init__(self, credentials_file: str = "credentials.json"):
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # YouTube API settings
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.credentials_file = credentials_file
        
        # Upload settings
        self.max_retries = 3
        self.retriable_exceptions = (HttpError,)
        self.retriable_status_codes = [500, 502, 503, 504]
        
        # Initialize YouTube service
        self.youtube_service = self.authenticate()
    
    def authenticate(self):
        """
        Authenticate with YouTube API using OAuth 2.0
        
        Returns:
            YouTube service object
        """
        try:
            credentials = None
            
            # Load existing token if available
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    credentials = pickle.load(token)
            
            # If there are no valid credentials, request authorization
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        raise FileNotFoundError(f"Credentials file not found: {self.credentials_file}")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes)
                    credentials = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(credentials, token)
            
            # Build YouTube service
            service = build(self.api_service_name, self.api_version, 
                          credentials=credentials)
            
            self.logger.info("YouTube API authentication successful")
            return service
            
        except Exception as e:
            self.logger.error(f"Error authenticating with YouTube API: {e}")
            raise
    
    def upload_video(self, video_path: str, metadata: Dict, 
                    thumbnail_path: Optional[str] = None,
                    privacy_status: str = "public") -> Optional[str]:
        """
        Upload video to YouTube with metadata
        
        Args:
            video_path: Path to video file
            metadata: Video metadata dictionary
            thumbnail_path: Path to thumbnail image
            privacy_status: Video privacy status (public, private, unlisted)
            
        Returns:
            Video ID of uploaded video or None if failed
        """
        try:
            if not os.path.exists(video_path):
                self.logger.error(f"Video file not found: {video_path}")
                return None
            
            self.logger.info(f"Uploading video: {video_path}")
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': metadata.get('title', 'Movie Breakdown'),
                    'description': metadata.get('description', ''),
                    'tags': metadata.get('tags', []),
                    'categoryId': metadata.get('category_id', '24')  # Entertainment
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Create media upload object
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/mp4'
            )
            
            # Execute upload
            insert_request = self.youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            video_id = self.resumable_upload(insert_request)
            
            if video_id:
                self.logger.info(f"Video uploaded successfully: https://youtube.com/watch?v={video_id}")
                
                # Upload thumbnail if provided
                if thumbnail_path and os.path.exists(thumbnail_path):
                    self.upload_thumbnail(video_id, thumbnail_path)
                
                return video_id
            else:
                self.logger.error("Video upload failed")
                return None
                
        except Exception as e:
            self.logger.error(f"Error uploading video: {e}")
            return None
    
    def resumable_upload(self, insert_request):
        """
        Execute resumable upload with retry logic
        
        Args:
            insert_request: YouTube API insert request
            
        Returns:
            Video ID or None if failed
        """
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                
                if response is not None:
                    if 'id' in response:
                        return response['id']
                    else:
                        self.logger.error(f"Upload failed with unexpected response: {response}")
                        return None
                        
            except HttpError as e:
                if e.resp.status in self.retriable_status_codes:
                    error = f"Retriable HTTP error {e.resp.status}: {e.content}"
                else:
                    self.logger.error(f"Non-retriable HTTP error: {e}")
                    return None
                    
            except Exception as e:
                error = f"Unexpected error: {e}"
            
            if error is not None:
                self.logger.warning(f"Upload error (attempt {retry + 1}): {error}")
                retry += 1
                
                if retry > self.max_retries:
                    self.logger.error("Maximum retries exceeded")
                    return None
                
                # Exponential backoff
                max_delay = 2 ** retry
                delay = random.uniform(0, max_delay)
                self.logger.info(f"Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
        
        return None
    
    def upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """
        Upload custom thumbnail for video
        
        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(thumbnail_path):
                self.logger.error(f"Thumbnail file not found: {thumbnail_path}")
                return False
            
            self.logger.info(f"Uploading thumbnail for video {video_id}")
            
            # Create media upload for thumbnail
            media = MediaFileUpload(
                thumbnail_path,
                mimetype='image/jpeg',
                resumable=False
            )
            
            # Upload thumbnail
            request = self.youtube_service.thumbnails().set(
                videoId=video_id,
                media_body=media
            )
            
            response = request.execute()
            
            if response:
                self.logger.info("Thumbnail uploaded successfully")
                return True
            else:
                self.logger.error("Thumbnail upload failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error uploading thumbnail: {e}")
            return False
    
    def update_video_metadata(self, video_id: str, metadata: Dict) -> bool:
        """
        Update video metadata after upload
        
        Args:
            video_id: YouTube video ID
            metadata: Updated metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Updating metadata for video {video_id}")
            
            body = {
                'id': video_id,
                'snippet': {
                    'title': metadata.get('title', ''),
                    'description': metadata.get('description', ''),
                    'tags': metadata.get('tags', []),
                    'categoryId': metadata.get('category_id', '24')
                }
            }
            
            request = self.youtube_service.videos().update(
                part='snippet',
                body=body
            )
            
            response = request.execute()
            
            if response:
                self.logger.info("Video metadata updated successfully")
                return True
            else:
                self.logger.error("Video metadata update failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating video metadata: {e}")
            return False
    
    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """
        Get information about uploaded video
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video information dictionary or None if failed
        """
        try:
            request = self.youtube_service.videos().list(
                part='snippet,statistics,status',
                id=video_id
            )
            
            response = request.execute()
            
            if response.get('items'):
                video_info = response['items'][0]
                self.logger.info(f"Retrieved info for video {video_id}")
                return video_info
            else:
                self.logger.error(f"Video not found: {video_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting video info: {e}")
            return None
    
    def delete_video(self, video_id: str) -> bool:
        """
        Delete video from YouTube
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Deleting video {video_id}")
            
            request = self.youtube_service.videos().delete(id=video_id)
            request.execute()
            
            self.logger.info("Video deleted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting video: {e}")
            return False
    
    def get_channel_info(self) -> Optional[Dict]:
        """
        Get information about the authenticated channel
        
        Returns:
            Channel information dictionary or None if failed
        """
        try:
            request = self.youtube_service.channels().list(
                part='snippet,statistics',
                mine=True
            )
            
            response = request.execute()
            
            if response.get('items'):
                channel_info = response['items'][0]
                self.logger.info("Retrieved channel information")
                return channel_info
            else:
                self.logger.error("Channel information not found")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting channel info: {e}")
            return None
    
    def create_playlist(self, title: str, description: str = "") -> Optional[str]:
        """
        Create a new playlist
        
        Args:
            title: Playlist title
            description: Playlist description
            
        Returns:
            Playlist ID or None if failed
        """
        try:
            body = {
                'snippet': {
                    'title': title,
                    'description': description
                },
                'status': {
                    'privacyStatus': 'public'
                }
            }
            
            request = self.youtube_service.playlists().insert(
                part='snippet,status',
                body=body
            )
            
            response = request.execute()
            
            if response.get('id'):
                playlist_id = response['id']
                self.logger.info(f"Created playlist: {title} (ID: {playlist_id})")
                return playlist_id
            else:
                self.logger.error("Playlist creation failed")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating playlist: {e}")
            return None
    
    def add_video_to_playlist(self, video_id: str, playlist_id: str) -> bool:
        """
        Add video to playlist
        
        Args:
            video_id: YouTube video ID
            playlist_id: YouTube playlist ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            body = {
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
            
            request = self.youtube_service.playlistItems().insert(
                part='snippet',
                body=body
            )
            
            response = request.execute()
            
            if response:
                self.logger.info(f"Added video {video_id} to playlist {playlist_id}")
                return True
            else:
                self.logger.error("Failed to add video to playlist")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding video to playlist: {e}")
            return False

def main():
    """Test the YouTubeUploader functionality"""
    try:
        print("Testing YouTubeUploader...")
        
        # Check if credentials file exists
        if not os.path.exists("credentials.json"):
            print("Error: credentials.json not found")
            print("Please download OAuth 2.0 credentials from Google Cloud Console")
            print("and save as 'credentials.json' in the project root")
            return
        
        uploader = YouTubeUploader()
        
        # Test channel info
        print("Getting channel information...")
        channel_info = uploader.get_channel_info()
        if channel_info:
            channel_name = channel_info['snippet']['title']
            subscriber_count = channel_info['statistics'].get('subscriberCount', 'Hidden')
            print(f"Channel: {channel_name}")
            print(f"Subscribers: {subscriber_count}")
        
        print("YouTubeUploader initialization successful!")
        print("Note: Video upload test requires an actual video file")
        
    except Exception as e:
        print(f"Error running YouTubeUploader test: {e}")

if __name__ == "__main__":
    main() 