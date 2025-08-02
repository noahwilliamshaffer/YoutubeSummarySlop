"""
Video Builder Module
Merges audio narration, video clips, and captions using moviepy
"""

import os
import random
from moviepy.editor import *
from moviepy.config import check_requirements
from typing import List, Dict, Optional, Tuple
import logging
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class VideoBuilder:
    def __init__(self):
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Video settings
        self.target_resolution = (1920, 1080)  # Full HD
        self.target_fps = 24
        self.audio_fade_duration = 0.5
        
        # Text overlay settings
        self.title_font_size = 72
        self.subtitle_font_size = 48
        self.caption_font_size = 36
        
        try:
            check_requirements()
            self.logger.info("MoviePy requirements satisfied")
        except Exception as e:
            self.logger.warning(f"MoviePy requirements check failed: {e}")
    
    def build_video(self, audio_path: str, visuals: Dict, 
                   captions_path: Optional[str] = None,
                   output_path: str = "./output/final_video.mp4",
                   movie_title: str = "Movie Breakdown") -> Optional[str]:
        """
        Build final video from audio, visuals, and captions
        
        Args:
            audio_path: Path to narration audio file
            visuals: Dictionary of visual assets
            captions_path: Path to SRT caption file
            output_path: Output video path
            movie_title: Title for video overlay
            
        Returns:
            Path to final video or None if failed
        """
        try:
            self.logger.info(f"Building video: {movie_title}")
            
            # Create output directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Load audio
            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration
            
            self.logger.info(f"Audio duration: {total_duration:.2f} seconds")
            
            # Prepare video clips
            video_clips = self.prepare_video_clips(visuals, total_duration)
            
            if not video_clips:
                self.logger.error("No video clips available")
                return None
            
            # Create main video sequence
            main_video = self.create_video_sequence(video_clips, total_duration)
            
            # Add title overlay
            title_video = self.add_title_overlay(main_video, movie_title)
            
            # Set audio
            final_video = title_video.set_audio(audio_clip)
            
            # Add captions if available
            if captions_path and os.path.exists(captions_path):
                final_video = self.add_captions(final_video, captions_path)
            
            # Add transitions and effects
            final_video = self.add_transitions(final_video)
            
            # Render final video
            self.logger.info(f"Rendering video to: {output_path}")
            final_video.write_videofile(
                output_path,
                fps=self.target_fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                preset='medium',
                threads=4
            )
            
            # Cleanup
            audio_clip.close()
            final_video.close()
            
            self.logger.info(f"Video built successfully: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error building video: {e}")
            return None
    
    def prepare_video_clips(self, visuals: Dict, total_duration: float) -> List[VideoFileClip]:
        """
        Prepare and process video clips for the main sequence
        
        Args:
            visuals: Dictionary of visual assets
            total_duration: Target total duration
            
        Returns:
            List of processed video clips
        """
        try:
            video_clips = []
            available_videos = visuals.get('videos', []) + visuals.get('background_videos', [])
            
            if not available_videos:
                # Create a solid color background if no videos available
                self.logger.warning("No videos available, creating solid background")
                return [self.create_solid_background(total_duration)]
            
            self.logger.info(f"Processing {len(available_videos)} video files")
            
            for video_info in available_videos:
                try:
                    video_path = video_info.get('path', '')
                    if not os.path.exists(video_path):
                        continue
                    
                    # Load and process video clip
                    clip = VideoFileClip(video_path)
                    
                    # Resize to target resolution
                    clip = self.resize_clip_to_fit(clip)
                    
                    # Ensure reasonable duration (between 3-15 seconds)
                    clip_duration = min(max(clip.duration, 3), 15)
                    if clip.duration > clip_duration:
                        clip = clip.subclip(0, clip_duration)
                    
                    video_clips.append(clip)
                    
                except Exception as e:
                    self.logger.error(f"Error processing video clip {video_path}: {e}")
                    continue
            
            if not video_clips:
                # Fallback to solid background
                return [self.create_solid_background(total_duration)]
            
            return video_clips
            
        except Exception as e:
            self.logger.error(f"Error preparing video clips: {e}")
            return [self.create_solid_background(total_duration)]
    
    def create_video_sequence(self, video_clips: List[VideoFileClip], total_duration: float) -> VideoFileClip:
        """
        Create main video sequence from available clips
        
        Args:
            video_clips: List of video clips
            total_duration: Target duration
            
        Returns:
            Composed video sequence
        """
        try:
            if not video_clips:
                return self.create_solid_background(total_duration)
            
            # Calculate how to distribute clips across duration
            sequence_clips = []
            current_time = 0
            
            while current_time < total_duration:
                remaining_time = total_duration - current_time
                
                # Select random clip
                clip = random.choice(video_clips).copy()
                
                # Determine clip duration for this segment
                segment_duration = min(remaining_time, clip.duration, 8)  # Max 8 seconds per segment
                
                if segment_duration < 1:  # Skip very short segments
                    break
                
                # Trim clip to segment duration
                if clip.duration > segment_duration:
                    start_time = random.uniform(0, max(0, clip.duration - segment_duration))
                    clip = clip.subclip(start_time, start_time + segment_duration)
                
                # Set position in timeline
                clip = clip.set_start(current_time)
                
                # Add some visual effects randomly
                if random.random() < 0.3:  # 30% chance
                    clip = self.add_visual_effects(clip)
                
                sequence_clips.append(clip)
                current_time += segment_duration
            
            # Compose final sequence
            if len(sequence_clips) == 1:
                final_video = sequence_clips[0]
            else:
                final_video = CompositeVideoClip(sequence_clips)
            
            # Ensure exact duration
            if final_video.duration != total_duration:
                final_video = final_video.set_duration(total_duration)
            
            return final_video
            
        except Exception as e:
            self.logger.error(f"Error creating video sequence: {e}")
            return self.create_solid_background(total_duration)
    
    def resize_clip_to_fit(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Resize clip to fit target resolution maintaining aspect ratio
        
        Args:
            clip: Input video clip
            
        Returns:
            Resized clip
        """
        try:
            target_w, target_h = self.target_resolution
            clip_w, clip_h = clip.size
            
            # Calculate scaling to fit
            scale_w = target_w / clip_w
            scale_h = target_h / clip_h
            scale = max(scale_w, scale_h)  # Scale to fill
            
            # Resize clip
            new_w = int(clip_w * scale)
            new_h = int(clip_h * scale)
            
            resized_clip = clip.resize((new_w, new_h))
            
            # Center crop to target resolution
            if new_w > target_w or new_h > target_h:
                x_offset = (new_w - target_w) // 2
                y_offset = (new_h - target_h) // 2
                
                resized_clip = resized_clip.crop(
                    x1=x_offset, y1=y_offset,
                    x2=x_offset + target_w, y2=y_offset + target_h
                )
            
            return resized_clip
            
        except Exception as e:
            self.logger.error(f"Error resizing clip: {e}")
            return clip
    
    def add_title_overlay(self, video_clip: VideoFileClip, title: str) -> VideoFileClip:
        """
        Add title overlay to video
        
        Args:
            video_clip: Input video
            title: Title text
            
        Returns:
            Video with title overlay
        """
        try:
            # Create title text clip
            title_clip = TextClip(
                title,
                fontsize=self.title_font_size,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2
            ).set_position('center').set_duration(3).set_start(0)
            
            # Add fade in/out
            title_clip = title_clip.crossfadein(0.5).crossfadeout(0.5)
            
            # Composite with main video
            final_video = CompositeVideoClip([video_clip, title_clip])
            
            return final_video
            
        except Exception as e:
            self.logger.error(f"Error adding title overlay: {e}")
            return video_clip
    
    def add_captions(self, video_clip: VideoFileClip, captions_path: str) -> VideoFileClip:
        """
        Add captions to video from SRT file
        
        Args:
            video_clip: Input video
            captions_path: Path to SRT file
            
        Returns:
            Video with captions
        """
        try:
            import pysrt
            
            # Load SRT file
            subs = pysrt.open(captions_path)
            
            caption_clips = []
            
            for sub in subs:
                # Convert timedelta to seconds
                start_time = sub.start.total_seconds()
                end_time = sub.end.total_seconds()
                duration = end_time - start_time
                
                if duration <= 0:
                    continue
                
                # Create text clip for caption
                caption_text = sub.text.replace('\n', ' ')
                
                caption_clip = TextClip(
                    caption_text,
                    fontsize=self.caption_font_size,
                    color='white',
                    font='Arial',
                    stroke_color='black',
                    stroke_width=1
                ).set_position(('center', 'bottom')).set_start(start_time).set_duration(duration)
                
                caption_clips.append(caption_clip)
            
            if caption_clips:
                # Composite captions with video
                final_video = CompositeVideoClip([video_clip] + caption_clips)
                self.logger.info(f"Added {len(caption_clips)} caption segments")
                return final_video
            
            return video_clip
            
        except Exception as e:
            self.logger.error(f"Error adding captions: {e}")
            return video_clip
    
    def add_transitions(self, video_clip: VideoFileClip) -> VideoFileClip:
        """
        Add smooth transitions and effects
        
        Args:
            video_clip: Input video
            
        Returns:
            Video with transitions
        """
        try:
            # Add fade in/out
            video_with_fades = video_clip.fadein(1).fadeout(1)
            
            return video_with_fades
            
        except Exception as e:
            self.logger.error(f"Error adding transitions: {e}")
            return video_clip
    
    def add_visual_effects(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Add random visual effects to clip
        
        Args:
            clip: Input clip
            
        Returns:
            Clip with effects
        """
        try:
            effects = ['blur', 'brightness', 'contrast']
            effect = random.choice(effects)
            
            if effect == 'blur':
                # Slight blur effect
                return clip.fx(vfx.blur, 1)
            elif effect == 'brightness':
                # Slight brightness adjustment
                return clip.fx(vfx.colorx, 1.1)
            elif effect == 'contrast':
                # Slight contrast adjustment
                return clip.fx(vfx.colorx, 0.9)
            
            return clip
            
        except Exception as e:
            self.logger.error(f"Error adding visual effects: {e}")
            return clip
    
    def create_solid_background(self, duration: float, color: Tuple[int, int, int] = (20, 20, 30)) -> VideoFileClip:
        """
        Create solid color background clip
        
        Args:
            duration: Clip duration
            color: RGB color tuple
            
        Returns:
            Solid color video clip
        """
        try:
            # Create solid color clip
            solid_clip = ColorClip(
                size=self.target_resolution,
                color=color,
                duration=duration
            )
            
            return solid_clip
            
        except Exception as e:
            self.logger.error(f"Error creating solid background: {e}")
            # Fallback: create very basic clip
            return ColorClip(size=(1920, 1080), color=(0, 0, 0), duration=duration)
    
    def create_thumbnail(self, video_path: str, movie_title: str, 
                        thumbnail_path: str = None) -> Optional[str]:
        """
        Create YouTube thumbnail from video
        
        Args:
            video_path: Path to video file
            movie_title: Movie title for overlay
            thumbnail_path: Output thumbnail path
            
        Returns:
            Path to thumbnail or None if failed
        """
        try:
            if not thumbnail_path:
                thumbnail_path = video_path.replace('.mp4', '_thumbnail.jpg')
            
            # Extract frame from video
            video = VideoFileClip(video_path)
            frame_time = min(5, video.duration / 2)  # Extract frame from middle or 5s
            frame = video.get_frame(frame_time)
            
            # Convert to PIL Image
            image = Image.fromarray(frame)
            
            # Resize to YouTube thumbnail size
            image = image.resize((1280, 720), Image.Resampling.LANCZOS)
            
            # Add title overlay
            draw = ImageDraw.Draw(image)
            
            # Try to use a bold font
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            # Add text with outline
            text_color = (255, 255, 255)
            outline_color = (0, 0, 0)
            
            # Calculate text position
            bbox = draw.textbbox((0, 0), movie_title, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (image.width - text_width) // 2
            y = image.height - text_height - 50
            
            # Draw text with outline
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), movie_title, font=font, fill=outline_color)
            
            draw.text((x, y), movie_title, font=font, fill=text_color)
            
            # Save thumbnail
            image.save(thumbnail_path, 'JPEG', quality=95)
            
            video.close()
            
            self.logger.info(f"Created thumbnail: {thumbnail_path}")
            return thumbnail_path
            
        except Exception as e:
            self.logger.error(f"Error creating thumbnail: {e}")
            return None

def main():
    """Test the VideoBuilder functionality"""
    try:
        builder = VideoBuilder()
        
        print("Testing VideoBuilder...")
        
        # Test solid background creation
        print("Creating test solid background...")
        bg_clip = builder.create_solid_background(5.0)
        print(f"Background clip duration: {bg_clip.duration}s")
        
        # Test basic video building (without actual files)
        print("VideoBuilder initialization successful!")
        print("Note: Full video building test requires actual audio and video files")
        
        bg_clip.close()
        
    except Exception as e:
        print(f"Error running VideoBuilder test: {e}")

if __name__ == "__main__":
    main() 