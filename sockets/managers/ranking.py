"""
Ranking logic for Live Quiz Socket.IO Server

Handles:
- Ranking calculation with tie support
- Winner determination
- Scoreboard generation
"""

from typing import Any

from .sessions import StudentData


class RankingManager:
    """Manager class for ranking-related operations."""

    @staticmethod
    def rank_players(students: dict[str, StudentData]) -> list[dict[str, Any]]:
        """
        Calculate rankings with tie support.

        Players with equal scores receive the same position.
        Example:
            Umar = 120  -> position 1
            Ali = 120   -> position 1
            Madina = 80 -> position 2
            Daler = 60  -> position 3
            Karim = 60  -> position 3

        Args:
            students: Dictionary of students {sid: StudentData}

        Returns:
            List of ranked players with name, score, and position
        """
        if not students:
            return []

        # Convert to list and sort by score descending
        player_list = [
            {"sid": sid, "name": data["name"], "score": data["score"]}
            for sid, data in students.items()
        ]
        player_list.sort(key=lambda x: x["score"], reverse=True)

        # Assign positions with tie handling
        ranked = []
        current_position = 1
        previous_score = None

        for i, player in enumerate(player_list):
            # If score is different from previous, update position
            if previous_score is not None and player["score"] < previous_score:
                current_position = i + 1

            ranked.append({
                "name": player["name"],
                "score": player["score"],
                "position": current_position,
                "sid": player["sid"],
            })

            previous_score = player["score"]

        return ranked

    @staticmethod
    def get_winners(students: dict[str, StudentData]) -> list[dict[str, Any]]:
        """
        Get all players with the highest score (multiple winners possible).

        Args:
            students: Dictionary of students {sid: StudentData}

        Returns:
            List of winners with name and score
        """
        if not students:
            return []

        # Find the maximum score
        max_score = max(data["score"] for data in students.values())

        # Get all players with the maximum score
        winners = [
            {"name": data["name"], "score": data["score"]}
            for sid, data in students.items()
            if data["score"] == max_score
        ]

        return winners

    @staticmethod
    def build_ranking_payload(students: dict[str, StudentData]) -> dict[str, Any]:
        """
        Build the ranking payload to send to teacher.

        Args:
            students: Dictionary of students {sid: StudentData}

        Returns:
            Formatted ranking payload
        """
        ranked = RankingManager.rank_players(students)

        # Remove sid from the payload sent to clients
        players = [
            {
                "name": player["name"],
                "score": player["score"],
                "position": player["position"],
            }
            for player in ranked
        ]

        return {
            "type": "ranking",
            "players": players,
        }

    @staticmethod
    def build_quiz_finished_payload(
        students: dict[str, StudentData]
    ) -> dict[str, Any]:
        """
        Build the quiz finished payload with winners and scoreboard.

        Args:
            students: Dictionary of students {sid: StudentData}

        Returns:
            Formatted quiz finished payload
        """
        winners = RankingManager.get_winners(students)
        ranked = RankingManager.rank_players(students)

        # Build scoreboard without sid
        scoreboard = [
            {
                "name": player["name"],
                "score": player["score"],
                "position": player["position"],
            }
            for player in ranked
        ]

        return {
            "type": "quiz_finished",
            "winners": winners,
            "scoreboard": scoreboard,
        }
