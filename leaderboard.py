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
            return window.submitScore(player_name, score)
        except Exception as e:
            logger.error(f"Error submitting score: {str(e)}")
            return None

async def submit_score_and_wait(player_name, score):
    """
    Submit a score to the leaderboard and wait for the submission to complete.
    
    Args:
        player_name: The name of the player (personality)
        score: The score to submit
        
    Returns:
        bool: True if the submission completed successfully, False otherwise
    """
    if IS_WEB:
        try:
            from js import window
            import asyncio
            
            logger.info(f"Submitting score and waiting: {player_name} - {score}")
            
            # Get initial leaderboard state
            initial_data = window.leaderboardData
            
            # Submit the score
            _ = submit_score(player_name, score)
            
            # Wait for leaderboard data to be updated
            for _ in range(20):  # Try for up to ~2 seconds (20 * 0.1s)
                await asyncio.sleep(0.1)
                
                # Check if leaderboard data has been updated 
                current_data = window.leaderboardData
                if current_data and (initial_data != current_data):
                    logger.info("Leaderboard data has been updated after score submission")
                    return True
                
            logger.warning("Timed out waiting for leaderboard update")
            # Force a fetch as a fallback
            fetch_leaderboard()
            return False
        except Exception as e:
            logger.error(f"Error in submit_score_and_wait: {str(e)}")
            # Force a fetch as a fallback
            fetch_leaderboard()
            return False

def on_leaderboard_fetch(result):
    """Callback for when leaderboard data is fetched"""
    update_leaderboard_display()

def fetch_leaderboard():
    """Fetch leaderboard data from JavaScript"""
    if IS_WEB:
        try:
            from js import window
            logger.info("Fetching leaderboard data")
            promise = window.fetchLeaderboard()
            promise.then(on_leaderboard_fetch)
        except Exception as e:
            logger.error(f"Error fetching leaderboard: {str(e)}")