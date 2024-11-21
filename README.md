# Discord-Bot
A Discord bot system that integrates with ProxyAI-Tavern.

## Features

- Image generation with multiple AI models
- Member verification system
- Docker containerized deployment
- Rate limiting for image generation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/locmaymo/Discord-Bot.git
```

2. Navigate to the project directory:
```bash
cd Discord-Bot
```

3. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
pip install -r bot-image/requirements.txt
pip install -r bot-SillyTavern/requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env` and update with your tokens:
```
BOT_PROXYAI_ARTIST=your_bot_token_1
BOT_SILLYTAVERN=your_bot_token_2
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_id
CLOUDFLARE_API_TOKEN=your_cloudflare_token
```

## Usage

Using Docker:
```bash
docker-compose up
```

Or run individually:
```bash
python bot-image/ProxyAI-Artist.py
python bot-SillyTavern/SillyTavern.py
```

## License

This project is licensed under the MIT License.