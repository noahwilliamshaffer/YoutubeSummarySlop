"""
Main Orchestrator for YouTube Movie Automation System
Coordinates all modules to generate and upload movie breakdown videos
"""

import os
import sys
import schedule
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add modules directory to path
sys.path.append('./modules')

# Import our modules
from movie_scraper import MovieScraper
from script_writer import ScriptWriter
from narration import NarrationGenerator
from visual_collector import VisualCollector
from caption_gen import CaptionGenerator
from video_builder import VideoBuilder
from youtube_uploader import YouTubeUploader

# Load environment variables
load_dotenv()

class YouTubeMovieAutomation:
    def __init__(self):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('automation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize modules
        try:
            self.movie_scraper = MovieScraper()
            self.script_writer = ScriptWriter()
            self.narrator = NarrationGenerator()
            self.visual_collector = VisualCollector()
            self.caption_generator = CaptionGenerator()
            self.video_builder = VideoBuilder()
            self.youtube_uploader = YouTubeUploader()
            
            self.logger.info("All modules initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing modules: {e}")
            raise
        
        # Configuration
        self.output_dir = os.getenv('VIDEO_OUTPUT_PATH', './output')
        self.temp_dir = os.getenv('TEMP_FILES_PATH', './temp')
        self.upload_schedule_hours = int(os.getenv('UPLOAD_SCHEDULE_HOURS', 8))
        
        # Ensure directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(f"{self.temp_dir}/visuals", exist_ok=True)
        
        # Playlist for organizing videos
        self.playlist_id = None
    
    def generate_video(self) -> bool:
        """
        Generate a complete movie breakdown video
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Starting video generation process...")
            
            # Step 1: Select a movie
            self.logger.info("Step 1: Selecting movie for breakdown...")
            movie_data = self.movie_scraper.select_movie_for_breakdown()
            
            if not movie_data:
                self.logger.error("Failed to select movie")
                return False
            
            movie_title = movie_data.get('title', 'Unknown Movie')
            self.logger.info(f"Selected movie: {movie_title}")
            
            # Step 2: Generate script
            self.logger.info("Step 2: Generating script...")
            script = self.script_writer.generate_script(movie_data)
            
            if not script:
                self.logger.error("Failed to generate script")
                return False
            
            # Format script for narration
            formatted_script = self.script_writer.format_script_for_narration(script)
            
            # Save script
            script_path = os.path.join(self.temp_dir, f"{movie_title.replace(' ', '_')}_script.txt")
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            
            self.logger.info(f"Script generated ({len(script)} characters)")
            
            # Step 3: Generate narration
            self.logger.info("Step 3: Generating narration...")
            audio_path = os.path.join(self.temp_dir, f"{movie_title.replace(' ', '_')}_narration.mp3")
            
            # Use timing-aware narration if possible
            timing_info = self.narrator.generate_speech_with_timestamps(
                formatted_script, 
                output_path=audio_path
            )
            
            if not timing_info:
                # Fallback to regular narration
                audio_path = self.narrator.generate_speech(
                    formatted_script,
                    output_path=audio_path
                )
                if audio_path:
                    timing_info = {'audio_path': audio_path, 'duration': 0}
            
            if not audio_path:
                self.logger.error("Failed to generate narration")
                return False
            
            self.logger.info(f"Narration generated: {audio_path}")
            
            # Step 4: Collect visuals
            self.logger.info("Step 4: Collecting visual assets...")
            visuals = self.visual_collector.collect_movie_visuals(
                movie_data, 
                output_dir=f"{self.temp_dir}/visuals"
            )
            
            total_visuals = (len(visuals['videos']) + len(visuals['images']) + 
                           len(visuals['background_videos']))
            
            if total_visuals == 0:
                self.logger.warning("No visuals collected, proceeding with generated backgrounds")
            else:
                self.logger.info(f"Collected {total_visuals} visual assets")
            
            # Step 5: Generate captions
            self.logger.info("Step 5: Generating captions...")
            captions_path = os.path.join(self.temp_dir, f"{movie_title.replace(' ', '_')}_captions.srt")
            
            if timing_info and timing_info.get('word_timestamps'):
                captions_path = self.caption_generator.generate_captions_from_timestamps(
                    script, timing_info, captions_path
                )
            else:
                captions_path = self.caption_generator.generate_estimated_captions(
                    script, timing_info or {'duration': 600}, captions_path  # Estimate 10 minutes
                )
            
            if captions_path:
                self.logger.info(f"Captions generated: {captions_path}")
            else:
                self.logger.warning("Failed to generate captions, proceeding without them")
            
            # Step 6: Build video
            self.logger.info("Step 6: Building final video...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"{movie_title.replace(' ', '_')}_{timestamp}.mp4"
            video_path = os.path.join(self.output_dir, video_filename)
            
            final_video_path = self.video_builder.build_video(
                audio_path=audio_path,
                visuals=visuals,
                captions_path=captions_path,
                output_path=video_path,
                movie_title=movie_title
            )
            
            if not final_video_path:
                self.logger.error("Failed to build video")
                return False
            
            self.logger.info(f"Video built successfully: {final_video_path}")
            
            # Step 7: Create thumbnail
            self.logger.info("Step 7: Creating thumbnail...")
            thumbnail_path = self.video_builder.create_thumbnail(
                final_video_path, 
                movie_title
            )
            
            # Step 8: Generate metadata for YouTube
            self.logger.info("Step 8: Preparing for YouTube upload...")
            metadata = self.script_writer.generate_video_metadata(movie_data, script)
            
            # Step 9: Upload to YouTube
            self.logger.info("Step 9: Uploading to YouTube...")
            video_id = self.youtube_uploader.upload_video(
                video_path=final_video_path,
                metadata=metadata,
                thumbnail_path=thumbnail_path,
                privacy_status="public"
            )
            
            if video_id:
                self.logger.info(f"Video uploaded successfully: https://youtube.com/watch?v={video_id}")
                
                # Add to playlist if exists
                if self.playlist_id:
                    self.youtube_uploader.add_video_to_playlist(video_id, self.playlist_id)
                
                # Step 10: Cleanup temporary files
                self.cleanup_temp_files(movie_title)
                
                return True
            else:
                self.logger.error("Failed to upload video to YouTube")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in video generation process: {e}")
            return False
    
    def cleanup_temp_files(self, movie_title: str):
        """
        Clean up temporary files after successful upload
        
        Args:
            movie_title: Movie title for file identification
        """
        try:
            safe_title = movie_title.replace(' ', '_')
            temp_patterns = [
                f"{safe_title}_script.txt",
                f"{safe_title}_narration.mp3",
                f"{safe_title}_captions.srt"
            ]
            
            files_removed = 0
            for pattern in temp_patterns:
                file_path = os.path.join(self.temp_dir, pattern)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    files_removed += 1
            
            # Clean up visual files (more complex cleanup)
            visual_dirs = ['videos', 'images', 'backgrounds', 'transitions']
            for dir_name in visual_dirs:
                dir_path = os.path.join(self.temp_dir, 'visuals', dir_name)
                if os.path.exists(dir_path):
                    for file in os.listdir(dir_path):
                        file_path = os.path.join(dir_path, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            files_removed += 1
            
            self.logger.info(f"Cleaned up {files_removed} temporary files")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {e}")
    
    def setup_playlist(self):
        """Set up a playlist for organizing uploaded videos"""
        try:
            playlist_title = "Movie Breakdowns - Automated Series"
            playlist_description = """
            Automated movie breakdown and analysis videos created using AI.
            
            Each video provides in-depth analysis of popular and trending movies,
            covering plot, characters, themes, and technical aspects.
            
            New videos uploaded regularly!
            """
            
            self.playlist_id = self.youtube_uploader.create_playlist(
                playlist_title, playlist_description
            )
            
            if self.playlist_id:
                self.logger.info(f"Created playlist: {playlist_title}")
            else:
                self.logger.warning("Failed to create playlist")
                
        except Exception as e:
            self.logger.error(f"Error setting up playlist: {e}")
    
    def run_once(self):
        """Run the video generation process once"""
        self.logger.info("=== Starting single video generation ===")
        success = self.generate_video()
        if success:
            self.logger.info("=== Video generation completed successfully ===")
        else:
            self.logger.error("=== Video generation failed ===")
        return success
    
    def run_scheduled(self):
        """Run the automation system with scheduling"""
        self.logger.info(f"Starting scheduled automation (every {self.upload_schedule_hours} hours)")
        
        # Setup playlist on first run
        self.setup_playlist()
        
        # Schedule the job
        schedule.every(self.upload_schedule_hours).hours.do(self.generate_video)
        
        # Run immediately on startup
        self.logger.info("Running initial video generation...")
        self.generate_video()
        
        # Keep running scheduled jobs
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def test_all_modules(self):
        """Test all modules individually"""
        self.logger.info("=== Testing all modules ===")
        
        try:
            # Test movie scraper
            self.logger.info("Testing MovieScraper...")
            trending_movies = self.movie_scraper.get_trending_movies()
            self.logger.info(f"✓ MovieScraper: Found {len(trending_movies)} trending movies")
            
            # Test script writer (using sample data)
            self.logger.info("Testing ScriptWriter...")
            sample_movie = {
                'title': 'Test Movie',
                'overview': 'A test movie for script generation',
                'genres': [{'name': 'Drama'}],
                'credits': {'crew': [{'name': 'Test Director', 'job': 'Director'}], 'cast': []}
            }
            # Note: This would use OpenAI API
            self.logger.info("✓ ScriptWriter: Module initialized (skipping API test)")
            
            # Test narration generator
            self.logger.info("Testing NarrationGenerator...")
            voices = self.narrator.get_available_voices()
            self.logger.info(f"✓ NarrationGenerator: Found {len(voices)} available voices")
            
            # Test visual collector
            self.logger.info("Testing VisualCollector...")
            test_videos = self.visual_collector.search_videos("test", per_page=1)
            self.logger.info(f"✓ VisualCollector: Found {len(test_videos)} test videos")
            
            # Test other modules
            self.logger.info("✓ CaptionGenerator: Module initialized")
            self.logger.info("✓ VideoBuilder: Module initialized")
            
            # Test YouTube uploader
            self.logger.info("Testing YouTubeUploader...")
            channel_info = self.youtube_uploader.get_channel_info()
            if channel_info:
                channel_name = channel_info['snippet']['title']
                self.logger.info(f"✓ YouTubeUploader: Connected to channel '{channel_name}'")
            else:
                self.logger.warning("⚠ YouTubeUploader: Could not get channel info")
            
            self.logger.info("=== All module tests completed ===")
            
        except Exception as e:
            self.logger.error(f"Error testing modules: {e}")

def main():
    """Main entry point"""
    try:
        # Initialize the automation system
        automation = YouTubeMovieAutomation()
        
        # Check command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "test":
                automation.test_all_modules()
            elif command == "once":
                automation.run_once()
            elif command == "schedule":
                automation.run_scheduled()
            else:
                print("Usage: python main.py [test|once|schedule]")
                print("  test     - Test all modules")
                print("  once     - Generate one video")
                print("  schedule - Run with scheduling (default)")
        else:
            # Default: run with scheduling
            automation.run_scheduled()
            
    except KeyboardInterrupt:
        print("\nAutomation stopped by user")
    except Exception as e:
        print(f"Error running automation: {e}")

if __name__ == "__main__":
    main() 