# 🤖 AI Trading Assistant Setup Guide

Your crypto trading simulator now has an AI-powered assistant! Here are your options:

## 🚀 Quick Start (Recommended: Ollama - Free & Local)

### Option 1: Ollama (Free, runs locally)
1. **Install Ollama**: Visit [ollama.ai](https://ollama.ai) and download for your OS
2. **Install a model**: Run in terminal:
   ```bash
   ollama pull llama3.2
   ```
3. **Start Ollama**: It should start automatically, or run:
   ```bash
   ollama serve
   ```
4. **Configure**: Your `.env` file is already set to use Ollama by default!
5. **Test**: Start your server and visit `/assistant`

### Option 2: Groq (Free tier, cloud-based, very fast)
1. **Get API key**: Visit [console.groq.com](https://console.groq.com/keys)
2. **Sign up** for free account
3. **Copy your API key**
4. **Update `.env`**:
   ```
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_api_key_here
   ```

### Option 3: OpenAI ChatGPT (Paid, most capable)
1. **Get API key**: Visit [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. **Add payment method** (required for API access)
3. **Copy your API key**
4. **Update `.env`**:
   ```
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your_api_key_here
   ```

## 🧪 Testing Your Setup

1. **Start your server**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Visit the assistant**: Go to `http://localhost:8000/assistant`

3. **Try these questions**:
   - "What is my overall portfolio performance?"
   - "Which coin should I sell first?"
   - "How can I improve my portfolio?"

## 🔧 Troubleshooting

### Ollama Issues:
- **"Connection refused"**: Make sure Ollama is running (`ollama serve`)
- **"Model not found"**: Install a model (`ollama pull llama3.2`)
- **Slow responses**: Normal for first run, gets faster

### API Issues:
- **"Invalid API key"**: Check your key in `.env` file
- **"Rate limit"**: Wait a moment and try again
- **"Insufficient quota"**: Add payment method (OpenAI) or check free tier limits (Groq)

### General Issues:
- **"LLM unavailable"**: Check your `.env` configuration
- **Fallback responses**: The assistant will use basic responses if LLM fails

## 🎯 What the Assistant Can Do

- **Portfolio Analysis**: Analyze your holdings and performance
- **Trading Advice**: Get insights on buying/selling decisions
- **Market Context**: Understand your coins in market context
- **Risk Assessment**: Evaluate portfolio diversification
- **Performance Insights**: Understand ROI and trends

## 💡 Pro Tips

1. **Be specific**: "Should I sell my Bitcoin?" vs "What should I do?"
2. **Ask follow-ups**: The assistant remembers your portfolio context
3. **Try different providers**: Each has different strengths
4. **Privacy**: Ollama keeps everything local, APIs send data to providers

## 🔒 Privacy & Security

- **Ollama**: Everything stays on your computer
- **Groq/OpenAI**: Your questions and portfolio data are sent to their servers
- **API Keys**: Keep them secret, don't share or commit to git
- **Portfolio Data**: Only summary data is sent, not personal info

Enjoy your new AI trading assistant! 🚀📈
