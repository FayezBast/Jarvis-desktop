import webbrowser
import urllib.parse
import requests
import re
from langchain.tools import tool

@tool
def youtube_search(query: str) -> str:
    """Search YouTube for videos and play the first result."""
    try:
        # Encode the search query for URL
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        # Get the search results page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(search_url, headers=headers)
        
        # Find the first video ID in the search results
        video_id_pattern = r'"videoId":"([^"]+)"'
        match = re.search(video_id_pattern, response.text)
        
        if match:
            video_id = match.group(1)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            webbrowser.open(video_url)
            return f"Found and playing YouTube video for '{query}': {video_url}"
        else:
            # Fallback to search results if no video found
            webbrowser.open(search_url)
            return f"Opened YouTube search for '{query}' - please select a video to play."
            
    except Exception as e:
        # Fallback to search results if anything fails
        try:
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            webbrowser.open(search_url)
            return f"Opened YouTube search for '{query}' (direct play failed: {str(e)})"
        except:
            return f"Failed to search YouTube: {str(e)}"

@tool
def play_youtube_video(video_url: str) -> str:
    """Play a specific YouTube video URL."""
    try:
        if "youtube.com" not in video_url and "youtu.be" not in video_url:
            return "Please provide a valid YouTube URL (youtube.com or youtu.be)."
        
        webbrowser.open(video_url)
        return f"Playing YouTube video: {video_url}"
    except Exception as e:
        return f"Failed to play YouTube video: {str(e)}"
