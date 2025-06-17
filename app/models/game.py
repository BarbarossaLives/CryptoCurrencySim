from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Enum
from app.models.db import Base
from datetime import datetime
import enum


class GameMode(enum.Enum):
    ROI_TARGET = "roi_target"
    NET_WORTH_TARGET = "net_worth_target"
    TIME_CHALLENGE = "time_challenge"
    SURVIVAL = "survival"


class GameStatus(enum.Enum):
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"
    PAUSED = "paused"


class AchievementType(enum.Enum):
    FIRST_TRADE = "first_trade"
    PROFIT_MILESTONE = "profit_milestone"
    PORTFOLIO_DIVERSITY = "portfolio_diversity"
    TRADING_STREAK = "trading_streak"
    RISK_MANAGEMENT = "risk_management"
    AI_FOLLOWER = "ai_follower"
    DIAMOND_HANDS = "diamond_hands"
    DAY_TRADER = "day_trader"


class GameSession(Base):
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(100), default="Anonymous Trader")
    
    # Game Configuration
    mode = Column(Enum(GameMode), default=GameMode.ROI_TARGET)
    status = Column(Enum(GameStatus), default=GameStatus.ACTIVE)
    
    # Starting Conditions
    starting_capital = Column(Float, default=5000.0)
    current_capital = Column(Float, default=5000.0)
    
    # Win Conditions
    target_roi = Column(Float, default=100.0)  # 100% ROI to win
    target_net_worth = Column(Float, default=10000.0)  # $10k to win
    target_days = Column(Integer, default=30)  # 30 days challenge
    
    # Progress Tracking
    current_roi = Column(Float, default=0.0)
    current_net_worth = Column(Float, default=5000.0)
    days_played = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    profitable_trades = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    last_played = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Game Stats
    highest_portfolio_value = Column(Float, default=5000.0)
    lowest_portfolio_value = Column(Float, default=5000.0)
    total_profit_loss = Column(Float, default=0.0)
    ai_suggestions_followed = Column(Integer, default=0)
    ai_suggestions_ignored = Column(Integer, default=0)
    
    # Difficulty & Bonuses
    difficulty_level = Column(String(20), default="Normal")  # Easy, Normal, Hard, Expert
    bonus_multiplier = Column(Float, default=1.0)
    
    def calculate_win_progress(self):
        """Calculate progress towards win condition"""
        if self.mode == GameMode.ROI_TARGET:
            return min(100, (self.current_roi / self.target_roi) * 100)
        elif self.mode == GameMode.NET_WORTH_TARGET:
            return min(100, (self.current_net_worth / self.target_net_worth) * 100)
        elif self.mode == GameMode.TIME_CHALLENGE:
            return min(100, (self.days_played / self.target_days) * 100)
        return 0
    
    def check_win_condition(self):
        """Check if player has won"""
        if self.mode == GameMode.ROI_TARGET:
            return self.current_roi >= self.target_roi
        elif self.mode == GameMode.NET_WORTH_TARGET:
            return self.current_net_worth >= self.target_net_worth
        elif self.mode == GameMode.TIME_CHALLENGE:
            return self.days_played >= self.target_days and self.current_roi > 0
        return False
    
    def get_win_description(self):
        """Get description of win condition"""
        if self.mode == GameMode.ROI_TARGET:
            return f"Reach {self.target_roi}% ROI"
        elif self.mode == GameMode.NET_WORTH_TARGET:
            return f"Reach ${self.target_net_worth:,.0f} net worth"
        elif self.mode == GameMode.TIME_CHALLENGE:
            return f"Stay profitable for {self.target_days} days"
        return "Unknown challenge"


class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    game_session_id = Column(Integer, index=True)
    
    # Achievement Details
    type = Column(Enum(AchievementType))
    name = Column(String(100))
    description = Column(Text)
    icon = Column(String(10))  # Emoji icon
    
    # Achievement Data
    target_value = Column(Float, nullable=True)  # Target for milestone achievements
    current_value = Column(Float, default=0.0)
    is_unlocked = Column(Boolean, default=False)
    
    # Rewards
    xp_reward = Column(Integer, default=100)
    bonus_cash = Column(Float, default=0.0)
    
    # Timestamps
    unlocked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def check_unlock_condition(self, game_session, portfolio_data=None):
        """Check if achievement should be unlocked"""
        if self.is_unlocked:
            return False
            
        if self.type == AchievementType.FIRST_TRADE:
            return game_session.total_trades >= 1
        elif self.type == AchievementType.PROFIT_MILESTONE:
            return game_session.total_profit_loss >= self.target_value
        elif self.type == AchievementType.PORTFOLIO_DIVERSITY:
            if portfolio_data:
                return len(portfolio_data.get('coins', [])) >= self.target_value
        elif self.type == AchievementType.TRADING_STREAK:
            return game_session.profitable_trades >= self.target_value
        elif self.type == AchievementType.AI_FOLLOWER:
            return game_session.ai_suggestions_followed >= self.target_value
        elif self.type == AchievementType.DIAMOND_HANDS:
            return game_session.days_played >= self.target_value
        elif self.type == AchievementType.DAY_TRADER:
            return game_session.total_trades >= self.target_value
        
        return False


class GameLeaderboard(Base):
    __tablename__ = "game_leaderboard"
    
    id = Column(Integer, primary_key=True, index=True)
    game_session_id = Column(Integer, index=True)
    
    # Player Info
    player_name = Column(String(100))
    
    # Performance Metrics
    final_roi = Column(Float)
    final_net_worth = Column(Float)
    days_to_complete = Column(Integer, nullable=True)
    total_trades = Column(Integer)
    win_rate = Column(Float)  # Percentage of profitable trades
    
    # Game Info
    game_mode = Column(Enum(GameMode))
    difficulty = Column(String(20))
    achievements_count = Column(Integer, default=0)
    
    # Timestamps
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# Default achievements to create for new games
DEFAULT_ACHIEVEMENTS = [
    {
        "type": AchievementType.FIRST_TRADE,
        "name": "First Steps",
        "description": "Make your first trade",
        "icon": "🎯",
        "target_value": 1,
        "xp_reward": 100
    },
    {
        "type": AchievementType.PROFIT_MILESTONE,
        "name": "Profit Maker",
        "description": "Make $500 in profit",
        "icon": "💰",
        "target_value": 500,
        "xp_reward": 250,
        "bonus_cash": 100
    },
    {
        "type": AchievementType.PROFIT_MILESTONE,
        "name": "Big Winner",
        "description": "Make $2000 in profit",
        "icon": "🏆",
        "target_value": 2000,
        "xp_reward": 500,
        "bonus_cash": 250
    },
    {
        "type": AchievementType.PORTFOLIO_DIVERSITY,
        "name": "Diversified",
        "description": "Hold 5 different cryptocurrencies",
        "icon": "🌈",
        "target_value": 5,
        "xp_reward": 200
    },
    {
        "type": AchievementType.TRADING_STREAK,
        "name": "Hot Streak",
        "description": "Make 5 profitable trades",
        "icon": "🔥",
        "target_value": 5,
        "xp_reward": 300
    },
    {
        "type": AchievementType.AI_FOLLOWER,
        "name": "AI Whisperer",
        "description": "Follow 10 AI suggestions",
        "icon": "🤖",
        "target_value": 10,
        "xp_reward": 200
    },
    {
        "type": AchievementType.DIAMOND_HANDS,
        "name": "Diamond Hands",
        "description": "Play for 7 consecutive days",
        "icon": "💎",
        "target_value": 7,
        "xp_reward": 400
    },
    {
        "type": AchievementType.DAY_TRADER,
        "name": "Day Trader",
        "description": "Make 20 trades",
        "icon": "⚡",
        "target_value": 20,
        "xp_reward": 350
    }
]
