import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
import httpx


class LLMService:
    """
    LLM service supporting multiple providers:
    - OpenAI (ChatGPT) - requires API key
    - Ollama - free, runs locally
    - Groq - free tier available
    """
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
    async def get_trading_advice(self, question: str, portfolio_data: Dict[str, Any], transactions: list, game_stats=None) -> str:
        """
        Get trading advice from LLM with portfolio context
        """
        try:
            # Prepare context for the LLM
            context = self._prepare_portfolio_context(portfolio_data, transactions)

            # Add game context if available
            if game_stats:
                context += self._prepare_game_context(game_stats)

            # Create the prompt
            prompt = self._create_prompt(question, context, game_stats)
            
            # Get response based on provider
            if self.provider == "openai" and self.openai_api_key:
                return await self._query_openai(prompt)
            elif self.provider == "groq" and self.groq_api_key:
                return await self._query_groq(prompt)
            elif self.provider == "ollama":
                return await self._query_ollama(prompt)
            else:
                return self._fallback_response(question, portfolio_data)
                
        except Exception as e:
            print(f"LLM Error: {e}")
            return self._fallback_response(question, portfolio_data)
    
    def _prepare_portfolio_context(self, portfolio_data: Dict[str, Any], transactions: list) -> str:
        """Prepare portfolio data as context for the LLM"""
        context = f"""
PORTFOLIO SUMMARY:
- Total Invested: ${portfolio_data.get('total_invested', 0)}
- Current Value: ${portfolio_data.get('total_current', 0)}
- Overall ROI: {portfolio_data.get('overall_roi', 0)}%

HOLDINGS:
"""
        
        for coin in portfolio_data.get('coins', []):
            context += f"- {coin['symbol']}: {coin['amount']} coins, ROI: {coin['roi']}%, Current Value: ${coin['current_value']}\n"
        
        if portfolio_data.get('top_gainer'):
            context += f"\nTop Performer: {portfolio_data['top_gainer']['symbol']} ({portfolio_data['top_gainer']['roi']}%)"
        
        if portfolio_data.get('top_loser'):
            context += f"\nWorst Performer: {portfolio_data['top_loser']['symbol']} ({portfolio_data['top_loser']['roi']}%)"
        
        # Add recent transactions
        if transactions:
            context += f"\n\nRECENT TRANSACTIONS (last 5):\n"
            for tx in transactions[:5]:
                context += f"- {tx.type.upper()} {abs(tx.amount)} {tx.symbol} at ${tx.price_usd} on {tx.timestamp.strftime('%Y-%m-%d')}\n"
        
        return context

    def _prepare_game_context(self, game_stats) -> str:
        """Prepare game-specific context for the LLM"""
        if not game_stats or not game_stats.get('game'):
            return ""

        game = game_stats['game']
        context = f"""

GAME CHALLENGE:
- Mode: {game.get_win_description()}
- Current Progress: {game_stats.get('progress_percentage', 0):.1f}%
- Difficulty: {game.difficulty_level}
- Days Played: {game_stats.get('days_since_start', 0)}
- Total Trades: {game.total_trades}
- Win Rate: {(game.profitable_trades / max(game.total_trades, 1)) * 100:.1f}%

ACHIEVEMENTS:
- Unlocked: {game_stats.get('achievements', {}).get('unlocked', 0)}/{game_stats.get('achievements', {}).get('total', 0)}
"""

        # Add recent achievements
        recent_achievements = [a for a in game_stats.get('achievements', {}).get('list', []) if a.is_unlocked]
        if recent_achievements:
            context += "\nRecent Achievements:\n"
            for achievement in recent_achievements[-3:]:  # Last 3 achievements
                context += f"- {achievement.icon} {achievement.name}: {achievement.description}\n"

        # Add win condition status
        if game_stats.get('is_winning'):
            context += "\n🎉 CONGRATULATIONS! You've reached your goal!"
        elif game_stats.get('progress_percentage', 0) > 75:
            context += "\n🔥 You're very close to winning! Keep it up!"
        elif game_stats.get('progress_percentage', 0) > 50:
            context += "\n📈 You're making good progress towards your goal!"

        return context

    def _create_prompt(self, question: str, context: str, game_stats=None) -> str:
        """Create the prompt for the LLM"""
        base_prompt = """You are an expert cryptocurrency trading assistant and game coach. You help users analyze their portfolio, make informed trading decisions, and achieve their game objectives."""

        if game_stats:
            base_prompt += """ You're also helping them succeed in their trading challenge game - acknowledge their progress, celebrate achievements, and provide strategic advice to help them reach their goals."""

        return f"""{base_prompt}

Current Portfolio & Game Context:
{context}

User Question: {question}

Please provide helpful, accurate advice based on the portfolio and game data. Be specific about their holdings and game progress when relevant. Keep responses concise but informative and motivating. If they're in a game, acknowledge their achievements and progress. Always remind users that this is not financial advice and they should do their own research.

Response:"""

    async def _query_openai(self, prompt: str) -> str:
        """Query OpenAI API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"OpenAI API error: {response.status_code}")

    async def _query_groq(self, prompt: str) -> str:
        """Query Groq API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"Groq API error: {response.status_code}")

    async def _query_ollama(self, prompt: str) -> str:
        """Query local Ollama instance"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2",  # Now using the proper conversational model
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 500
                    }
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["response"].strip()
            else:
                raise Exception(f"Ollama error: {response.status_code}")

    def _fallback_response(self, question: str, portfolio_data: Dict[str, Any]) -> str:
        """Fallback response when LLM is unavailable"""
        q = question.lower()
        
        if "roi" in q:
            return f"Your overall ROI is {portfolio_data.get('overall_roi', 0)}%. This shows how your portfolio is performing compared to your initial investment."
        
        elif "best" in q or "top" in q:
            top = portfolio_data.get("top_gainer")
            if top:
                return f"Your top performing coin is {top['symbol']} with an ROI of {top['roi']}%. Consider monitoring this asset's momentum."
        
        elif "worst" in q or "loss" in q:
            low = portfolio_data.get("top_loser")
            if low:
                return f"Your worst performing coin is {low['symbol']} with an ROI of {low['roi']}%. You might want to research recent developments for this asset."
        
        else:
            # Try coin-specific lookup
            for coin in portfolio_data.get("coins", []):
                if coin["symbol"].lower() in q:
                    return f"{coin['symbol']} has an ROI of {coin['roi']}% and current value of ${coin['current_value']}. This represents {coin['amount']} coins at an average buy price of ${coin['price_usd']}."
        
        return "I'm currently unable to connect to the AI assistant. Please check your LLM configuration. In the meantime, you can view your portfolio summary above for basic insights."


# Global instance
llm_service = LLMService()
