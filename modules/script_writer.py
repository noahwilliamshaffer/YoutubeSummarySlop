"""
Script Writer Module
Generates engaging 1500-2500 word movie breakdown scripts using OpenAI GPT-4
"""

import os
import openai
from dotenv import load_dotenv
from typing import Dict, Optional
import logging
import json

# Load environment variables
load_dotenv()

class ScriptWriter:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file")
        
        # Initialize OpenAI client
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # System prompt for script generation
        self.system_prompt = """
You are a YouTube movie breakdown scriptwriter with millions of subscribers.
Create a structured 1500–2500 word video script for a 10–20 minute YouTube video analyzing a movie.
Avoid major spoilers unless specifically in the "Ending Explained" section.

REQUIRED STRUCTURE:
1. Hook (engaging, 2–3 sentences that grab attention immediately)
2. Intro & Background (director, genre, cast, reception, why it matters)
3. Plot Summary (high-level overview without major spoilers)
4. Characters & Performances (key characters and standout performances)
5. Themes & Symbolism (deeper meaning, messages, cultural significance)
6. Technical Aspects (cinematography, music, direction highlights)
7. Ending Explained (SPOILER WARNING - detailed ending analysis)
8. Final Takeaway & Viewer Question (wrap-up and engagement prompt)

TONE: Conversational, slightly cinematic, emotionally engaging, enthusiastic but analytical.
STYLE: Use rhetorical questions, build suspense, include specific examples, make it feel like a discussion with a film-savvy friend.
LENGTH: Aim for 1500-2500 words (approximately 10-15 minutes of narration).

Include natural transitions between sections and maintain viewer engagement throughout.
"""
    
    def generate_script(self, movie_data: Dict) -> Optional[str]:
        """
        Generate a movie breakdown script based on movie data
        
        Args:
            movie_data: Dictionary containing movie information from TMDb
            
        Returns:
            Generated script text or None if failed
        """
        try:
            # Extract key information from movie data
            title = movie_data.get('title', 'Unknown Movie')
            overview = movie_data.get('overview', '')
            release_date = movie_data.get('release_date', '')
            rating = movie_data.get('vote_average', 0)
            runtime = movie_data.get('runtime', 0)
            genres = [g.get('name', '') for g in movie_data.get('genres', [])]
            
            # Extract director and main cast
            credits = movie_data.get('credits', {})
            director = "Unknown Director"
            if credits.get('crew'):
                for person in credits['crew']:
                    if person.get('job') == 'Director':
                        director = person.get('name', 'Unknown Director')
                        break
            
            main_cast = []
            if credits.get('cast'):
                main_cast = [person.get('name', '') for person in credits['cast'][:5]]
            
            # Create the user prompt with movie details
            user_prompt = f"""
Write a comprehensive movie breakdown script for: {title}

MOVIE DETAILS:
- Title: {title}
- Director: {director}
- Release Date: {release_date}
- Rating: {rating}/10
- Runtime: {runtime} minutes
- Genres: {', '.join(genres)}
- Main Cast: {', '.join(main_cast)}
- Plot Overview: {overview}

Create an engaging, analytical breakdown that would work perfectly for a YouTube movie analysis channel.
Focus on what makes this movie special, memorable moments, and deeper meanings.
Remember to include the spoiler warning before the ending explanation section.
"""

            self.logger.info(f"Generating script for movie: {title}")
            
            # Generate the script using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.7
            )
            
            script = response.choices[0].message.content
            
            if script:
                self.logger.info(f"Successfully generated script ({len(script)} characters)")
                return script
            else:
                self.logger.error("Generated script is empty")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating script: {e}")
            return None
    
    def format_script_for_narration(self, script: str) -> str:
        """
        Format the script for better text-to-speech narration
        
        Args:
            script: Raw script text
            
        Returns:
            Formatted script optimized for TTS
        """
        try:
            # Clean up formatting for better TTS
            formatted_script = script.replace('\n\n', '\n')
            formatted_script = formatted_script.replace('**', '')
            formatted_script = formatted_script.replace('*', '')
            
            # Add pauses for better pacing
            formatted_script = formatted_script.replace('. ', '. ... ')
            formatted_script = formatted_script.replace('? ', '? ... ')
            formatted_script = formatted_script.replace('! ', '! ... ')
            
            # Add longer pauses for section breaks
            formatted_script = formatted_script.replace('\n', ' ... ... ')
            
            self.logger.info("Script formatted for narration")
            return formatted_script
            
        except Exception as e:
            self.logger.error(f"Error formatting script: {e}")
            return script
    
    def generate_video_metadata(self, movie_data: Dict, script: str) -> Dict:
        """
        Generate YouTube video metadata based on movie and script
        
        Args:
            movie_data: Movie information
            script: Generated script
            
        Returns:
            Dictionary containing video metadata
        """
        try:
            title = movie_data.get('title', 'Unknown Movie')
            release_year = movie_data.get('release_date', '')[:4] if movie_data.get('release_date') else ''
            genres = [g.get('name', '') for g in movie_data.get('genres', [])]
            
            # Generate video title
            video_title = f"{title} ({release_year}) - Complete Movie Breakdown & Analysis"
            
            # Generate description
            description = f"""
🎬 In-depth breakdown and analysis of {title} ({release_year})

Join us for a comprehensive dive into this {', '.join(genres[:2]).lower()} film, exploring its themes, characters, cinematography, and deeper meanings.

⚠️ SPOILER WARNING: This video contains detailed plot discussion including the ending.

🎯 What's Covered:
• Plot summary and key moments
• Character analysis and performances  
• Themes and symbolism
• Technical aspects and direction
• Ending explained in detail
• Final thoughts and takeaways

💬 What did you think of {title}? Let us know in the comments!

🔔 Subscribe for more movie breakdowns and film analysis!

#MovieBreakdown #{title.replace(' ', '')} #FilmAnalysis #MovieReview #Cinema
"""
            
            # Generate tags
            tags = [
                title.lower(),
                'movie breakdown',
                'film analysis',
                'movie review',
                'cinema',
                'movie explained',
                'ending explained'
            ]
            
            # Add genre tags
            tags.extend([genre.lower() for genre in genres])
            
            metadata = {
                'title': video_title,
                'description': description.strip(),
                'tags': tags[:50],  # YouTube allows max 50 tags
                'category_id': '24',  # Entertainment category
                'privacy_status': 'public'
            }
            
            self.logger.info(f"Generated metadata for video: {video_title}")
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error generating video metadata: {e}")
            return {
                'title': f"{movie_data.get('title', 'Movie')} - Breakdown",
                'description': 'Movie analysis and breakdown',
                'tags': ['movie', 'breakdown'],
                'category_id': '24',
                'privacy_status': 'public'
            }
    
    def save_script(self, script: str, movie_title: str, output_dir: str = "./temp") -> Optional[str]:
        """
        Save the generated script to a file
        
        Args:
            script: Generated script text
            movie_title: Movie title for filename
            output_dir: Output directory
            
        Returns:
            Path to saved file or None if failed
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Clean movie title for filename
            safe_title = "".join(c for c in movie_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')
            
            filename = f"{safe_title}_script.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(script)
            
            self.logger.info(f"Script saved to: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving script: {e}")
            return None

def main():
    """Test the ScriptWriter functionality"""
    try:
        # Sample movie data for testing
        sample_movie = {
            'title': 'The Matrix',
            'overview': 'A computer hacker learns from mysterious rebels about the true nature of his reality.',
            'release_date': '1999-03-31',
            'vote_average': 8.7,
            'runtime': 136,
            'genres': [{'name': 'Action'}, {'name': 'Science Fiction'}],
            'credits': {
                'crew': [{'name': 'The Wachowskis', 'job': 'Director'}],
                'cast': [
                    {'name': 'Keanu Reeves'},
                    {'name': 'Laurence Fishburne'},
                    {'name': 'Carrie-Anne Moss'}
                ]
            }
        }
        
        writer = ScriptWriter()
        
        print("Generating script for sample movie...")
        script = writer.generate_script(sample_movie)
        
        if script:
            print(f"Script generated successfully!")
            print(f"Length: {len(script)} characters")
            print(f"Preview: {script[:200]}...")
            
            # Test metadata generation
            metadata = writer.generate_video_metadata(sample_movie, script)
            print(f"\nGenerated metadata:")
            print(f"Title: {metadata['title']}")
            print(f"Tags: {', '.join(metadata['tags'][:5])}...")
            
        else:
            print("Failed to generate script")
            
    except Exception as e:
        print(f"Error running ScriptWriter test: {e}")

if __name__ == "__main__":
    main() 