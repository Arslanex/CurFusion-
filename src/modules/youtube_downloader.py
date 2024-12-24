import os
import re
import yt_dlp

class YoutubeDownloader:
    def __init__(self, download_path=None):
        if download_path is None:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            download_path = os.path.join(root_dir, "downloads")

        self.download_path = download_path

    def validate_youtube_link(self, link):
        # Validate if the provided link is a valid YouTube URL
        print(f"Validating YouTube link: {link}")
        youtube_regex = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$')
        is_valid = bool(youtube_regex.match(link))
        print(f"Link validation result: {is_valid}")
        return is_valid

    def download_video(self, link):
        # Download the video from YouTube using yt-dlp
        print(f"Downloading video from link: {link}")
        if not self.validate_youtube_link(link):
            print("Invalid YouTube link detected")
            raise ValueError("Invalid YouTube link")

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',  # Download best video and audio available
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            # Save with video title and correct extension
            'merge_output_format': 'mp4',  # Ensure the output format is mp4
            'noplaylist': True  # Ensure only single video is downloaded
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                video_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp4"

                # Ensure the video path exists
                if not os.path.exists(video_path):
                    # Try alternative path generation
                    video_path = os.path.join(
                        self.download_path,
                        f"{info.get('title', 'unknown')}.mp4"
                    )

                # Construct metadata dictionary
                metadata = {
                    "title": info.get("title", "Unknown Title"),
                    "duration": info.get("duration", 0),
                    "views": info.get("view_count", 0),
                    "author": info.get("uploader", "Unknown Author"),
                    "file_path": video_path,
                    "url": link
                }

                print(f"Video downloaded successfully: {metadata}")
                return metadata

        except Exception as e:
            print(f"Error downloading video: {e}")
            raise

if __name__ == "__main__":
    module = YoutubeDownloader()
    youtube_link = input("Enter the YouTube link: ")

    try:
        print("Starting video download process...")
        metadata = module.download_youtube_video(youtube_link, 'deneme')
        print("Video downloaded successfully:", metadata)
    except Exception as e:
        print("Error:", e)
