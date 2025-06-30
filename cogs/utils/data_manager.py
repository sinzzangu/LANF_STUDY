"""
Data Manager for Discord LOL Internal Match Bot
==============================================

Handles all data operations for users and matches using JSON files.

File: cogs/utils/data_manager.py
Author: Juan Dodam
Version: 1.0.0
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class DataManager:
    """Manages user and match data for the LOL internal match bot."""
    
    def __init__(self):
        """Initialize data manager with file paths."""
        self.data_dir = Path("data")
        self.users_file = self.data_dir / "users.json"
        self.matches_file = self.data_dir / "matches.json"
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize empty files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Create empty JSON files if they don't exist."""
        if not self.users_file.exists():
            self._save_json(self.users_file, {})
        if not self.matches_file.exists():
            self._save_json(self.matches_file, {})
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON data from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        """Save JSON data to file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ===== USER DATA METHODS =====
    
    def get_all_users(self) -> Dict[str, Any]:
        """Get all users data."""
        return self._load_json(self.users_file)
    
    def get_user(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific user data by name."""
        users = self.get_all_users()
        return users.get(name)
    
    def user_exists(self, name: str) -> bool:
        """Check if user exists."""
        return name in self.get_all_users()
    
    def add_user(self, name: str, tier: str, rank: str, main_position: str, 
                 sub_position: str, mmr: int = 1500) -> bool:
        """
        Add a new user.
        
        Args:
            name: User's real name
            tier: LOL tier (골드, 실버, etc.)
            rank: LOL rank (1, 2, 3, 4)
            main_position: Main position
            sub_position: Sub position
            mmr: Initial MMR (default 1500)
        
        Returns:
            bool: True if user was added, False if user already exists
        """
        if self.user_exists(name):
            return False
        
        users = self.get_all_users()
        users[name] = {
            "tier": tier,
            "rank": rank,
            "main_position": main_position,
            "sub_position": sub_position,
            "mmr": mmr,
            "wins": 0,
            "losses": 0,
            "total_games": 0
        }
        
        self._save_json(self.users_file, users)
        return True
    
    def update_user(self, name: str, **kwargs) -> bool:
        """
        Update user data.
        
        Args:
            name: User's name
            **kwargs: Fields to update
        
        Returns:
            bool: True if updated, False if user doesn't exist
        """
        if not self.user_exists(name):
            return False
        
        users = self.get_all_users()
        users[name].update(kwargs)
        self._save_json(self.users_file, users)
        return True
    
    def delete_user(self, name: str) -> bool:
        """Delete a user."""
        users = self.get_all_users()
        if name in users:
            del users[name]
            self._save_json(self.users_file, users)
            return True
        return False
    
    def update_user_stats(self, name: str, won: bool):
        """Update user's win/loss statistics."""
        if not self.user_exists(name):
            return False
        
        users = self.get_all_users()
        user = users[name]
        
        if won:
            user["wins"] += 1
        else:
            user["losses"] += 1
        
        user["total_games"] += 1
        
        self._save_json(self.users_file, users)
        return True
    
    def get_user_winrate(self, name: str) -> Optional[float]:
        """Get user's win rate percentage."""
        user = self.get_user(name)
        if not user or user["total_games"] == 0:
            return None
        
        return (user["wins"] / user["total_games"]) * 100
    
    # ===== MATCH DATA METHODS =====
    
    def get_all_matches(self) -> Dict[str, Any]:
        """Get all matches data."""
        return self._load_json(self.matches_file)
    
    def get_match(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get specific match data by ID."""
        matches = self.get_all_matches()
        return matches.get(match_id)
    
    def add_match(self, blue_team: List[str], red_team: List[str], 
                  winner: str, mvp: str, date: str = None) -> str:
        """
        Add a new match.
        
        Args:
            blue_team: List of blue team player names
            red_team: List of red team player names  
            winner: "blue" or "red"
            mvp: MVP player name
            date: Match date (defaults to today)
        
        Returns:
            str: Match ID
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        matches = self.get_all_matches()
        
        # Generate match ID
        match_count = len(matches) + 1
        match_id = f"match_{match_count:03d}"
        
        # Ensure unique match ID
        while match_id in matches:
            match_count += 1
            match_id = f"match_{match_count:03d}"
        
        matches[match_id] = {
            "date": date,
            "blue_team": blue_team,
            "red_team": red_team,
            "winner": winner,
            "mvp": mvp
        }
        
        self._save_json(self.matches_file, matches)
        
        # Update user statistics
        winning_team = blue_team if winner == "blue" else red_team
        losing_team = red_team if winner == "blue" else blue_team
        
        for player in winning_team:
            self.update_user_stats(player, True)
        
        for player in losing_team:
            self.update_user_stats(player, False)
        
        return match_id
    
    def get_user_matches(self, name: str) -> List[Dict[str, Any]]:
        """Get all matches where user participated."""
        matches = self.get_all_matches()
        user_matches = []
        
        for match_id, match_data in matches.items():
            if name in match_data["blue_team"] or name in match_data["red_team"]:
                match_info = match_data.copy()
                match_info["match_id"] = match_id
                user_matches.append(match_info)
        
        return user_matches
    
    def get_recent_matches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent matches."""
        matches = self.get_all_matches()
        
        # Sort by match_id (which includes chronological order)
        sorted_matches = sorted(matches.items(), reverse=True)
        
        recent = []
        for match_id, match_data in sorted_matches[:limit]:
            match_info = match_data.copy()
            match_info["match_id"] = match_id
            recent.append(match_info)
        
        return recent
    
    # ===== UTILITY METHODS =====
    
    def get_leaderboard(self, sort_by: str = "mmr") -> List[Dict[str, Any]]:
        """
        Get leaderboard sorted by specified field.
        
        Args:
            sort_by: Field to sort by (mmr, wins, winrate, total_games)
        
        Returns:
            List of users sorted by specified field
        """
        users = self.get_all_users()
        
        leaderboard = []
        for name, data in users.items():
            user_data = data.copy()
            user_data["name"] = name
            
            # Calculate win rate for sorting
            if sort_by == "winrate":
                if user_data["total_games"] > 0:
                    user_data["winrate"] = (user_data["wins"] / user_data["total_games"]) * 100
                else:
                    user_data["winrate"] = 0
        
            leaderboard.append(user_data)
        
        # Sort by specified field
        if sort_by in ["mmr", "wins", "total_games", "winrate"]:
            leaderboard.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
        
        return leaderboard
    
    def get_match_count(self) -> int:
        """Get total number of matches."""
        return len(self.get_all_matches())
    
    def get_user_count(self) -> int:
        """Get total number of users."""
        return len(self.get_all_users())


# Global instance
data_manager = DataManager()


# Helper functions for easy import
def get_data_manager() -> DataManager:
    """Get the global data manager instance."""
    return data_manager