from compat import IS_WEB
from logger import logger, get_module_logger

logger = get_module_logger('leaderboard')

def update_leaderboard_display():
    """Update the leaderboard display in the HTML"""
    if IS_WEB:
        try:
            from js import document, window
            
            leaderboard_data = window.leaderboardData
            if leaderboard_data:
                leaderboard_html = ""
                for i, entry in enumerate(leaderboard_data, 1):
                    leaderboard_html += f"""
                    <div class="leaderboard-entry">
                        <div class="rank-name">
                            <span class="rank">{i}</span>
                            <span class="name">{entry.player_name}</span>
                        </div>
                        <span class="score">{entry.score}</span>
                    </div>
                    """
                document.querySelector(".leaderboard-entries").innerHTML = leaderboard_html
                logger.info("Leaderboard display updated")
        except Exception as e:
            logger.error(f"Error updating leaderboard display: {str(e)}")

def submit_score(player_name, score):
    """Submit a score to the leaderboard"""
    if IS_WEB:
        try:
            from js import window
            logger.info(f"Submitting score: {player_name} - {score}")
            # Submit score and wait for it to complete
            window.submitScore(player_name, score)
            # Force an immediate fetch and update of the leaderboard
            fetch_leaderboard()
        except Exception as e:
            logger.error(f"Error submitting score: {str(e)}")

def on_leaderboard_fetch(result):
    """Callback for when leaderboard data is fetched"""
    logger.info("Leaderboard data fetched, updating display")
    update_leaderboard_display()

def fetch_leaderboard():
    """Fetch leaderboard data from JavaScript"""
    if IS_WEB:
        try:
            from js import window
            logger.info("Fetching leaderboard data")
            # Use callback-based approach with immediate update
            promise = window.fetchLeaderboard()
            promise.then(on_leaderboard_fetch)
            # Also update immediately with whatever data we have
            update_leaderboard_display()
        except Exception as e:
            logger.error(f"Error fetching leaderboard: {str(e)}")