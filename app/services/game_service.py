from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models.game import GameSession, Achievement, GameLeaderboard, DEFAULT_ACHIEVEMENTS
from app.models.game import GameMode, GameStatus, AchievementType
# Database session will be handled locally
from datetime import datetime, timedelta
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./crypto.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Global game session (simplified for single-player)
current_game_session = None


class GameService:
    def __init__(self):
        self.db = SessionLocal()
    
    def get_current_game(self):
        """Get the current active game session"""
        global current_game_session
        if current_game_session is None:
            # Try to find an active game
            game = self.db.query(GameSession).filter(
                GameSession.status == GameStatus.ACTIVE
            ).first()
            current_game_session = game
        return current_game_session
    
    def start_new_game(self, player_name="Anonymous Trader", mode=GameMode.ROI_TARGET, difficulty="Normal"):
        """Start a new game session"""
        global current_game_session

        # End any existing active games
        existing_games = self.db.query(GameSession).filter(
            GameSession.status == GameStatus.ACTIVE
        ).all()
        for game in existing_games:
            game.status = GameStatus.PAUSED

        # Clear existing portfolio and transactions for fresh start
        self._clear_portfolio_and_transactions()

        # Create new game session
        game_config = self._get_game_config(mode, difficulty)

        new_game = GameSession(
            player_name=player_name,
            mode=mode,
            status=GameStatus.ACTIVE,
            starting_capital=game_config["starting_capital"],
            current_capital=game_config["starting_capital"],
            current_net_worth=game_config["starting_capital"],
            target_roi=game_config["target_roi"],
            target_net_worth=game_config["target_net_worth"],
            target_days=game_config["target_days"],
            difficulty_level=difficulty,
            bonus_multiplier=game_config["bonus_multiplier"],
            highest_portfolio_value=game_config["starting_capital"],
            lowest_portfolio_value=game_config["starting_capital"]
        )

        self.db.add(new_game)
        self.db.commit()
        self.db.refresh(new_game)

        # Create default achievements
        self._create_default_achievements(new_game.id)

        current_game_session = new_game
        return new_game
    
    def _get_game_config(self, mode, difficulty):
        """Get game configuration based on mode and difficulty"""
        base_config = {
            "starting_capital": 5000.0,
            "bonus_multiplier": 1.0
        }
        
        # Mode-specific settings
        if mode == GameMode.ROI_TARGET:
            base_config.update({
                "target_roi": 100.0,  # 100% ROI
                "target_net_worth": 10000.0,
                "target_days": 30
            })
        elif mode == GameMode.NET_WORTH_TARGET:
            base_config.update({
                "target_roi": 200.0,
                "target_net_worth": 15000.0,  # $15k target
                "target_days": 45
            })
        elif mode == GameMode.TIME_CHALLENGE:
            base_config.update({
                "target_roi": 50.0,  # Just stay profitable
                "target_net_worth": 7500.0,
                "target_days": 14  # 2 week challenge
            })
        
        # Difficulty modifiers
        if difficulty == "Easy":
            base_config["starting_capital"] = 7500.0
            base_config["bonus_multiplier"] = 1.2
            base_config["target_roi"] *= 0.8
        elif difficulty == "Hard":
            base_config["starting_capital"] = 3000.0
            base_config["bonus_multiplier"] = 0.8
            base_config["target_roi"] *= 1.5
        elif difficulty == "Expert":
            base_config["starting_capital"] = 2000.0
            base_config["bonus_multiplier"] = 0.6
            base_config["target_roi"] *= 2.0
        
        return base_config

    def _clear_portfolio_and_transactions(self):
        """Clear all existing portfolio holdings and transaction history"""
        from app.models.db import Coin, Transaction

        # Clear all coins from portfolio
        self.db.query(Coin).delete()

        # Clear all transaction history
        self.db.query(Transaction).delete()

        # Commit the changes
        self.db.commit()

    def _create_default_achievements(self, game_session_id):
        """Create default achievements for a new game"""
        for achievement_data in DEFAULT_ACHIEVEMENTS:
            achievement = Achievement(
                game_session_id=game_session_id,
                **achievement_data
            )
            self.db.add(achievement)
        self.db.commit()
    
    def update_game_progress(self, portfolio_data, transaction_data=None):
        """Update game progress based on portfolio and transaction data"""
        game = self.get_current_game()
        if not game:
            return None
        
        # Update basic stats
        game.current_net_worth = portfolio_data.get('total_current', game.starting_capital)
        game.current_roi = portfolio_data.get('overall_roi', 0.0)
        game.total_profit_loss = game.current_net_worth - game.starting_capital
        game.last_played = datetime.utcnow()
        
        # Update high/low watermarks
        if game.current_net_worth > game.highest_portfolio_value:
            game.highest_portfolio_value = game.current_net_worth
        if game.current_net_worth < game.lowest_portfolio_value:
            game.lowest_portfolio_value = game.current_net_worth
        
        # Update trade counts if new transaction
        if transaction_data:
            game.total_trades += 1
            if transaction_data.get('profit', 0) > 0:
                game.profitable_trades += 1
        
        # Check win condition
        if game.check_win_condition():
            game.status = GameStatus.WON
            game.completed_at = datetime.utcnow()
            self._add_to_leaderboard(game)
        
        # Check achievements
        self._check_achievements(game, portfolio_data)
        
        self.db.commit()
        return game
    
    def _check_achievements(self, game, portfolio_data):
        """Check and unlock achievements"""
        achievements = self.db.query(Achievement).filter(
            Achievement.game_session_id == game.id,
            Achievement.is_unlocked == False
        ).all()
        
        newly_unlocked = []
        for achievement in achievements:
            if achievement.check_unlock_condition(game, portfolio_data):
                achievement.is_unlocked = True
                achievement.unlocked_at = datetime.utcnow()
                
                # Apply rewards
                if achievement.bonus_cash > 0:
                    game.current_capital += achievement.bonus_cash
                    game.current_net_worth += achievement.bonus_cash
                
                newly_unlocked.append(achievement)
        
        return newly_unlocked
    
    def _add_to_leaderboard(self, game):
        """Add completed game to leaderboard"""
        achievements_count = self.db.query(Achievement).filter(
            Achievement.game_session_id == game.id,
            Achievement.is_unlocked == True
        ).count()
        
        win_rate = 0
        if game.total_trades > 0:
            win_rate = (game.profitable_trades / game.total_trades) * 100
        
        days_to_complete = None
        if game.completed_at and game.started_at:
            days_to_complete = (game.completed_at - game.started_at).days
        
        leaderboard_entry = GameLeaderboard(
            game_session_id=game.id,
            player_name=game.player_name,
            final_roi=game.current_roi,
            final_net_worth=game.current_net_worth,
            days_to_complete=days_to_complete,
            total_trades=game.total_trades,
            win_rate=win_rate,
            game_mode=game.mode,
            difficulty=game.difficulty_level,
            achievements_count=achievements_count,
            completed_at=game.completed_at
        )
        
        self.db.add(leaderboard_entry)
    
    def get_achievements(self, game_session_id=None):
        """Get achievements for current game"""
        if not game_session_id:
            game = self.get_current_game()
            if not game:
                return []
            game_session_id = game.id
        
        return self.db.query(Achievement).filter(
            Achievement.game_session_id == game_session_id
        ).all()
    
    def get_leaderboard(self, mode=None, limit=10):
        """Get leaderboard entries"""
        query = self.db.query(GameLeaderboard)
        
        if mode:
            query = query.filter(GameLeaderboard.game_mode == mode)
        
        return query.order_by(
            GameLeaderboard.final_roi.desc(),
            GameLeaderboard.days_to_complete.asc()
        ).limit(limit).all()
    
    def record_ai_interaction(self, followed_suggestion=True):
        """Record AI assistant interaction"""
        game = self.get_current_game()
        if game:
            if followed_suggestion:
                game.ai_suggestions_followed += 1
            else:
                game.ai_suggestions_ignored += 1
            self.db.commit()
    
    def get_game_stats(self):
        """Get comprehensive game statistics"""
        game = self.get_current_game()
        if not game:
            return None
        
        achievements = self.get_achievements(game.id)
        unlocked_achievements = [a for a in achievements if a.is_unlocked]
        
        return {
            "game": game,
            "progress_percentage": game.calculate_win_progress(),
            "win_description": game.get_win_description(),
            "achievements": {
                "total": len(achievements),
                "unlocked": len(unlocked_achievements),
                "list": achievements
            },
            "days_since_start": (datetime.utcnow() - game.started_at).days,
            "is_winning": game.check_win_condition()
        }
    
    def reset_portfolio(self):
        """Reset portfolio to starting capital (useful for game restart)"""
        game = self.get_current_game()
        if game:
            # This would need to integrate with your existing portfolio service
            # to clear all holdings and reset to starting capital
            pass


# Global service instance
game_service = GameService()
