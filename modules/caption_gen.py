"""
Caption Generator Module
Generates synchronized captions from TTS timestamps and script text
"""

import os
import pysrt
from typing import List, Dict, Optional, Tuple
import logging
import re
from datetime import timedelta

class CaptionGenerator:
    def __init__(self):
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Caption formatting settings
        self.max_chars_per_line = 60
        self.max_lines_per_subtitle = 2
        self.min_duration_ms = 1000  # Minimum 1 second per subtitle
        self.max_duration_ms = 5000  # Maximum 5 seconds per subtitle
    
    def generate_captions_from_timestamps(self, script_text: str, 
                                        timing_info: Dict,
                                        output_path: str = "./temp/captions.srt") -> Optional[str]:
        """
        Generate SRT captions from script text and timing information
        
        Args:
            script_text: Original script text
            timing_info: Dictionary with word-level timestamps from TTS
            output_path: Path to save SRT file
            
        Returns:
            Path to generated SRT file or None if failed
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            word_timestamps = timing_info.get('word_timestamps', [])
            if not word_timestamps:
                # Fallback to estimated timing
                return self.generate_estimated_captions(script_text, timing_info, output_path)
            
            self.logger.info(f"Generating captions with {len(word_timestamps)} word timestamps")
            
            # Clean script text for processing
            cleaned_text = self.clean_script_text(script_text)
            words = cleaned_text.split()
            
            # Create subtitle items
            subtitle_items = []
            current_text = ""
            current_start_time = None
            current_end_time = None
            subtitle_index = 1
            
            for i, word_info in enumerate(word_timestamps):
                word = word_info.get('word', '').strip()
                start_time = word_info.get('start_time', 0)
                end_time = word_info.get('end_time', 0)
                
                if not word:
                    continue
                
                # Start new subtitle if this is the first word
                if current_start_time is None:
                    current_start_time = start_time
                    current_text = word
                    current_end_time = end_time
                    continue
                
                # Check if we should break into new subtitle
                potential_text = f"{current_text} {word}"
                
                should_break = (
                    len(potential_text) > self.max_chars_per_line * self.max_lines_per_subtitle or
                    (current_end_time - current_start_time) * 1000 > self.max_duration_ms or
                    self.is_sentence_end(current_text)
                )
                
                if should_break:
                    # Create subtitle item
                    subtitle_item = self.create_subtitle_item(
                        subtitle_index, current_text, current_start_time, current_end_time
                    )
                    if subtitle_item:
                        subtitle_items.append(subtitle_item)
                        subtitle_index += 1
                    
                    # Start new subtitle
                    current_start_time = start_time
                    current_text = word
                    current_end_time = end_time
                else:
                    # Continue current subtitle
                    current_text = potential_text
                    current_end_time = end_time
            
            # Add final subtitle
            if current_text and current_start_time is not None:
                subtitle_item = self.create_subtitle_item(
                    subtitle_index, current_text, current_start_time, current_end_time
                )
                if subtitle_item:
                    subtitle_items.append(subtitle_item)
            
            # Save SRT file
            srt_file = pysrt.SubRipFile(items=subtitle_items)
            srt_file.save(output_path, encoding='utf-8')
            
            self.logger.info(f"Generated {len(subtitle_items)} caption segments: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating captions from timestamps: {e}")
            return None
    
    def generate_estimated_captions(self, script_text: str, 
                                  timing_info: Dict,
                                  output_path: str) -> Optional[str]:
        """
        Generate captions with estimated timing when word-level timestamps aren't available
        
        Args:
            script_text: Script text
            timing_info: Basic timing information (total duration)
            output_path: Output SRT file path
            
        Returns:
            Path to generated SRT file
        """
        try:
            total_duration = timing_info.get('duration', 0)
            if total_duration <= 0:
                # Estimate duration based on text length (average speaking rate: 150 words/min)
                word_count = len(script_text.split())
                total_duration = (word_count / 150) * 60  # Convert to seconds
            
            self.logger.info(f"Generating estimated captions for {total_duration:.1f}s audio")
            
            # Clean and split text into segments
            cleaned_text = self.clean_script_text(script_text)
            segments = self.split_text_into_segments(cleaned_text)
            
            # Calculate timing for each segment
            subtitle_items = []
            time_per_segment = total_duration / len(segments)
            
            for i, segment in enumerate(segments):
                start_time = i * time_per_segment
                end_time = (i + 1) * time_per_segment
                
                # Adjust timing based on segment length
                segment_word_count = len(segment.split())
                estimated_segment_duration = (segment_word_count / 150) * 60
                
                if estimated_segment_duration < time_per_segment:
                    end_time = start_time + estimated_segment_duration
                
                subtitle_item = self.create_subtitle_item(i + 1, segment, start_time, end_time)
                if subtitle_item:
                    subtitle_items.append(subtitle_item)
            
            # Save SRT file
            srt_file = pysrt.SubRipFile(items=subtitle_items)
            srt_file.save(output_path, encoding='utf-8')
            
            self.logger.info(f"Generated {len(subtitle_items)} estimated caption segments: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating estimated captions: {e}")
            return None
    
    def create_subtitle_item(self, index: int, text: str, start_time: float, end_time: float) -> Optional[pysrt.SubRipItem]:
        """
        Create a subtitle item with proper formatting
        
        Args:
            index: Subtitle index
            text: Subtitle text
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            SubRipItem or None if invalid
        """
        try:
            # Ensure minimum duration
            duration_ms = (end_time - start_time) * 1000
            if duration_ms < self.min_duration_ms:
                end_time = start_time + (self.min_duration_ms / 1000)
            
            # Format text
            formatted_text = self.format_subtitle_text(text)
            if not formatted_text.strip():
                return None
            
            # Convert to timedelta objects
            start_td = timedelta(seconds=start_time)
            end_td = timedelta(seconds=end_time)
            
            # Create subtitle item
            item = pysrt.SubRipItem(
                index=index,
                start=start_td,
                end=end_td,
                text=formatted_text
            )
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error creating subtitle item: {e}")
            return None
    
    def format_subtitle_text(self, text: str) -> str:
        """
        Format text for subtitle display
        
        Args:
            text: Raw text
            
        Returns:
            Formatted subtitle text
        """
        try:
            # Clean text
            text = text.strip()
            
            # Break long lines
            if len(text) > self.max_chars_per_line:
                words = text.split()
                lines = []
                current_line = ""
                
                for word in words:
                    potential_line = f"{current_line} {word}".strip()
                    
                    if len(potential_line) <= self.max_chars_per_line:
                        current_line = potential_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                        
                        # Limit to max lines
                        if len(lines) >= self.max_lines_per_subtitle:
                            break
                
                if current_line and len(lines) < self.max_lines_per_subtitle:
                    lines.append(current_line)
                
                text = '\n'.join(lines)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error formatting subtitle text: {e}")
            return text
    
    def clean_script_text(self, text: str) -> str:
        """
        Clean script text for caption generation
        
        Args:
            text: Raw script text
            
        Returns:
            Cleaned text
        """
        try:
            # Remove TTS pause markers
            text = re.sub(r'\s*\.\.\.\s*', ' ', text)
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove formatting markers
            text = re.sub(r'\*+', '', text)
            text = re.sub(r'#+', '', text)
            
            # Clean up punctuation
            text = re.sub(r'\s+([,.!?])', r'\1', text)
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error cleaning script text: {e}")
            return text
    
    def split_text_into_segments(self, text: str) -> List[str]:
        """
        Split text into appropriate subtitle segments
        
        Args:
            text: Cleaned text
            
        Returns:
            List of text segments
        """
        try:
            # Split by sentences first
            sentences = re.split(r'[.!?]+', text)
            segments = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # If sentence is too long, split further
                if len(sentence) > self.max_chars_per_line * self.max_lines_per_subtitle:
                    # Split by clauses
                    clauses = re.split(r'[,;]+', sentence)
                    for clause in clauses:
                        clause = clause.strip()
                        if clause:
                            segments.append(clause)
                else:
                    segments.append(sentence)
            
            # Combine very short segments
            combined_segments = []
            current_segment = ""
            
            for segment in segments:
                potential_combined = f"{current_segment} {segment}".strip()
                
                if len(potential_combined) <= self.max_chars_per_line * self.max_lines_per_subtitle:
                    current_segment = potential_combined
                else:
                    if current_segment:
                        combined_segments.append(current_segment)
                    current_segment = segment
            
            if current_segment:
                combined_segments.append(current_segment)
            
            return combined_segments
            
        except Exception as e:
            self.logger.error(f"Error splitting text into segments: {e}")
            return [text]
    
    def is_sentence_end(self, text: str) -> bool:
        """
        Check if text ends with sentence-ending punctuation
        
        Args:
            text: Text to check
            
        Returns:
            True if text ends with sentence-ending punctuation
        """
        return bool(re.search(r'[.!?]\s*$', text.strip()))
    
    def generate_vtt_captions(self, srt_path: str, vtt_path: str = None) -> Optional[str]:
        """
        Convert SRT captions to WebVTT format
        
        Args:
            srt_path: Path to SRT file
            vtt_path: Output VTT path (auto-generated if None)
            
        Returns:
            Path to VTT file or None if failed
        """
        try:
            if not vtt_path:
                vtt_path = srt_path.replace('.srt', '.vtt')
            
            # Load SRT file
            srt_file = pysrt.open(srt_path)
            
            # Create VTT content
            vtt_content = "WEBVTT\n\n"
            
            for item in srt_file:
                start_time = self.format_vtt_time(item.start)
                end_time = self.format_vtt_time(item.end)
                
                vtt_content += f"{start_time} --> {end_time}\n"
                vtt_content += f"{item.text}\n\n"
            
            # Save VTT file
            with open(vtt_path, 'w', encoding='utf-8') as f:
                f.write(vtt_content)
            
            self.logger.info(f"Generated VTT captions: {vtt_path}")
            return vtt_path
            
        except Exception as e:
            self.logger.error(f"Error generating VTT captions: {e}")
            return None
    
    def format_vtt_time(self, td: timedelta) -> str:
        """
        Format timedelta for VTT format
        
        Args:
            td: Timedelta object
            
        Returns:
            Formatted time string
        """
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = td.microseconds // 1000
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

def main():
    """Test the CaptionGenerator functionality"""
    try:
        caption_gen = CaptionGenerator()
        
        # Sample script text
        sample_script = """
        Welcome to our movie breakdown series. Today we're diving deep into one of cinema's most 
        influential films. This movie changed everything about how we think about storytelling 
        and visual effects. Let's explore what makes this film so special and why it continues 
        to captivate audiences decades after its release.
        """
        
        # Sample timing info (simulated)
        sample_timing = {
            'duration': 15.0,
            'word_timestamps': [
                {'word': 'Welcome', 'start_time': 0.0, 'end_time': 0.5},
                {'word': 'to', 'start_time': 0.5, 'end_time': 0.7},
                {'word': 'our', 'start_time': 0.7, 'end_time': 0.9},
                {'word': 'movie', 'start_time': 0.9, 'end_time': 1.3},
                {'word': 'breakdown', 'start_time': 1.3, 'end_time': 1.8},
                {'word': 'series', 'start_time': 1.8, 'end_time': 2.3},
                # ... more timestamps would be here
            ]
        }
        
        print("Generating captions from sample script...")
        
        # Test caption generation
        srt_file = caption_gen.generate_captions_from_timestamps(
            sample_script, sample_timing, "./temp/test_captions.srt"
        )
        
        if srt_file:
            print(f"Captions generated: {srt_file}")
            
            # Test VTT conversion
            vtt_file = caption_gen.generate_vtt_captions(srt_file)
            if vtt_file:
                print(f"VTT captions generated: {vtt_file}")
        else:
            print("Failed to generate captions")
        
        # Test estimated captions
        estimated_srt = caption_gen.generate_estimated_captions(
            sample_script, {'duration': 15.0}, "./temp/estimated_captions.srt"
        )
        
        if estimated_srt:
            print(f"Estimated captions generated: {estimated_srt}")
        
    except Exception as e:
        print(f"Error running CaptionGenerator test: {e}")

if __name__ == "__main__":
    main() 