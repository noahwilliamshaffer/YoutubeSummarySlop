# 🔑 API Setup Guide

This guide will help you set up all the required API keys and services for the YouTube Movie Automation System.

## Required APIs

1. **OpenAI API** - For AI script generation
2. **TMDb API** - For movie data and trending information
3. **ElevenLabs API** - For AI voice generation
4. **Pexels API** - For royalty-free stock footage
5. **YouTube Data API v3** - For video upload

---

## 1. OpenAI API Setup

### Step 1: Create OpenAI Account
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or sign in to your account
3. Navigate to [API Keys](https://platform.openai.com/api-keys)

### Step 2: Generate API Key
1. Click "Create new secret key"
2. Give it a name (e.g., "YouTube Automation")
3. Copy the API key (starts with `sk-`)
4. Add to `.env` file: `OPENAI_API_KEY=sk-your-key-here`

### Step 3: Add Billing
1. Go to [Billing](https://platform.openai.com/account/billing)
2. Add a payment method
3. Set usage limits if desired

**Cost Estimate:** ~$0.50-2.00 per video (depending on script length)

---

## 2. TMDb (The Movie Database) API Setup

### Step 1: Create TMDb Account
1. Go to [TMDb](https://www.themoviedb.org/)
2. Create a free account
3. Go to [Settings > API](https://www.themoviedb.org/settings/api)

### Step 2: Request API Key
1. Click "Request an API Key"
2. Choose "Developer" option
3. Fill out the application form:
   - **Application Name:** YouTube Movie Automation
   - **Application URL:** Your GitHub repo URL
   - **Application Summary:** Automated movie breakdown videos
4. Accept terms and submit

### Step 3: Get Your API Key
1. Once approved (usually instant), copy your API key
2. Add to `.env` file: `TMDB_API_KEY=your-key-here`

**Cost:** Free (1000 requests per day)

---

## 3. ElevenLabs API Setup

### Step 1: Create ElevenLabs Account
1. Go to [ElevenLabs](https://elevenlabs.io/)
2. Sign up for an account
3. Go to [Profile Settings](https://elevenlabs.io/subscription)

### Step 2: Get API Key
1. Navigate to "Profile" → "API Key"
2. Copy your API key
3. Add to `.env` file: `ELEVENLABS_API_KEY=your-key-here`

### Step 3: Choose Voice
1. Go to [Voice Library](https://elevenlabs.io/voice-library)
2. Browse and test voices
3. Copy the Voice ID of your preferred voice
4. Add to `.env` file: `DEFAULT_VOICE_ID=voice-id-here`

**Popular Voice IDs:**
- `EXAVITQu4vr4xnSDxMaL` - Bella (calm, professional)
- `ErXwobaYiN019PkySvjV` - Antoni (deep, narrative)
- `MF3mGyEYCl7XYWbV9V6O` - Elli (energetic, young)

**Cost:** Free tier: 10,000 characters/month, Paid: $5+/month

---

## 4. Pexels API Setup

### Step 1: Create Pexels Account
1. Go to [Pexels](https://www.pexels.com/)
2. Create a free account
3. Go to [Pexels API](https://www.pexels.com/api/)

### Step 2: Request API Key
1. Click "Request API Access"
2. Fill out the form:
   - **Application Name:** YouTube Movie Automation
   - **Application Description:** Automated movie breakdown videos
   - **Application URL:** Your GitHub repo URL
3. Submit request

### Step 3: Get Your API Key
1. Check your email for approval (usually within 24 hours)
2. Copy your API key from the approval email
3. Add to `.env` file: `PEXELS_API_KEY=your-key-here`

**Cost:** Free (200 requests/hour, 20,000/month)

---

## 5. YouTube Data API v3 Setup

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Name it "YouTube Movie Automation"

### Step 2: Enable YouTube Data API
1. Go to "APIs & Services" → "Library"
2. Search for "YouTube Data API v3"
3. Click on it and press "Enable"

### Step 3: Create OAuth 2.0 Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. If prompted, configure OAuth consent screen:
   - Choose "External" user type
   - Fill required fields (app name, email)
   - Add your email to test users
4. Choose "Desktop Application" as application type
5. Name it "YouTube Automation Client"
6. Download the JSON file

### Step 4: Setup Credentials
1. Rename downloaded file to `credentials.json`
2. Place it in your project root directory
3. The system will handle OAuth flow on first run

**Cost:** Free (10,000 quota units per day, uploads cost 1600 units each)

---

## 6. Environment Configuration

Create a `.env` file in your project root with all your API keys:

```env
# OpenAI API
OPENAI_API_KEY=sk-your-openai-key-here

# TMDb API
TMDB_API_KEY=your-tmdb-key-here

# ElevenLabs API
ELEVENLABS_API_KEY=your-elevenlabs-key-here

# Pexels API
PEXELS_API_KEY=your-pexels-key-here

# Configuration
DEFAULT_VOICE_ID=EXAVITQu4vr4xnSDxMaL
VIDEO_OUTPUT_PATH=./output/
TEMP_FILES_PATH=./temp/
UPLOAD_SCHEDULE_HOURS=8
```

---

## 7. Testing Your Setup

Run the test command to verify all APIs are working:

```bash
python main.py test
```

This will test each API connection and report any issues.

---

## 🚨 Security Notes

1. **Never commit API keys** - They're ignored by `.gitignore`
2. **Set usage limits** on paid APIs to avoid unexpected charges
3. **Monitor usage** regularly through API dashboards
4. **Rotate keys** periodically for security

---

## 💰 Cost Breakdown (Estimated Monthly)

- **OpenAI:** $15-50 (depending on video count)
- **TMDb:** Free
- **ElevenLabs:** $5-25 (depending on voice quality)
- **Pexels:** Free
- **YouTube API:** Free
- **Total:** ~$20-75/month for 3 videos/day

---

## 🆘 Troubleshooting

### Common Issues:

**OpenAI API Error 429 (Rate Limit)**
- Solution: Add billing information or wait for rate limit reset

**TMDb API Returns Empty Results**
- Solution: Check API key format, ensure no extra spaces

**ElevenLabs API Error 401**
- Solution: Verify API key is correct and account has credits

**YouTube Upload Fails**
- Solution: Check `credentials.json` exists and OAuth is completed

**Pexels No Results**
- Solution: Try different search terms, check API quota

### Getting Help:

1. Check `automation.log` for detailed error messages
2. Verify all API keys in `.env` file
3. Test individual modules with their test functions
4. Check API service status pages

---

## 🎯 Next Steps

Once all APIs are configured:

1. Run `python setup.py` to verify installation
2. Test with `python main.py test`
3. Generate your first video with `python main.py once`
4. Start automation with `python main.py schedule`

Happy automating! 🚀 