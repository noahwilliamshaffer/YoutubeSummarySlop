# YouTube Movie Summary Automation 🎬

An automated system that generates and uploads movie breakdown videos to YouTube 3 times daily using AI.

## 🧱 System Architecture (Modular Stack)

| Module | Task | Tools |
|--------|------|-------|
| `movie_scraper.py` | Scrape trending movies | TMDb API |
| `script_writer.py` | Generate 1500–2500 word summary | OpenAI GPT-4 |
| `narration.py` | AI voice generation | ElevenLabs API |
| `caption_gen.py` | Generate synced captions | From TTS timestamps |
| `visual_collector.py` | Fetch royalty-free/AI visuals | Pexels API, DALL·E |
| `video_builder.py` | Merge voice + video + captions | moviepy/ffmpeg |
| `youtube_uploader.py` | Upload video to YouTube | YouTube Data API |
| `main.py` | Schedule & run 3x daily | Python scheduler |

## 🚀 Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/noahwilliamshaffer/YoutubeSummarySlop.git
   cd YoutubeSummarySlop
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Set up YouTube API credentials:**
   - Go to Google Cloud Console
   - Create a new project or select existing
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download credentials.json and place in project root

5. **Run the system:**
   ```bash
   python main.py
   ```

## 📋 Required API Keys

- **OpenAI API Key** - For script generation
- **TMDb API Key** - For movie data
- **ElevenLabs API Key** - For voice generation
- **Pexels API Key** - For stock footage
- **YouTube Data API** - For uploading videos

## 🎯 Features

- **Automated Movie Selection**: Scrapes trending movies from TMDb
- **AI Script Generation**: Creates engaging 1500-2500 word breakdowns
- **Professional Narration**: ElevenLabs AI voice generation
- **Dynamic Visuals**: Fetches relevant stock footage and images
- **Synchronized Captions**: Auto-generated captions for accessibility
- **Automatic Upload**: Uploads to YouTube with metadata
- **Scheduled Execution**: Runs 3 times daily automatically

## 📁 Project Structure

```
YoutubeSummarySlop/
├── main.py                 # Main orchestrator
├── modules/
│   ├── movie_scraper.py    # Movie data scraping
│   ├── script_writer.py    # AI script generation
│   ├── narration.py        # Voice generation
│   ├── caption_gen.py      # Caption creation
│   ├── visual_collector.py # Visual content fetching
│   ├── video_builder.py    # Video composition
│   └── youtube_uploader.py # YouTube upload
├── output/                 # Generated videos
├── temp/                   # Temporary files
├── credentials.json        # YouTube API credentials
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables
```

## 🔧 Configuration

Edit `.env` file to configure:
- API keys and credentials
- Output paths
- Upload schedule
- Voice preferences

## 📈 Output

- **Video Length**: 10-20 minutes
- **Quality**: HD (1080p)
- **Format**: MP4
- **Frequency**: 3 uploads per day
- **Content**: Movie breakdowns with analysis

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational purposes. Ensure compliance with YouTube's terms of service and copyright laws when using this automation system. 