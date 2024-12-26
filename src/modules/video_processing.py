import os
import subprocess
from typing import List, Dict, Optional

import moviepy.editor as mp

class VideoProcessor:
    def __init__(self, 
                 upload_folder: str = 'projects/videos', 
                 output_folder: str = 'projects/compiled_videos'):
        """
        Initialize VideoProcessor with upload and output directories
        
        :param upload_folder: Directory to store uploaded/downloaded videos
        :param output_folder: Directory to store processed videos
        """
        self.upload_folder = upload_folder
        self.output_folder = output_folder
        
        # Ensure directories exist
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)

    def extract_video_segment(self,
                              video_path: str,
                              start_time: float,
                              end_time: float) -> str:
        # Validate input
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Create output filename
        filename = f"segment_{start_time}_{end_time}.mp4"
        output_path = os.path.join(self.output_folder, filename)

        # Use moviepy for segment extraction
        with mp.VideoFileClip(video_path) as video:
            segment = video.subclip(start_time, end_time)

            # Burada sesle ilgili parametreleri ekliyoruz:
            segment.write_videofile(
                output_path,
                logger=None,
                codec="libx264",  # Video codec
                audio_codec="aac",  # Ses codec
                temp_audiofile="temp-audio.m4a",
                remove_temp=True
            )

        return output_path

    def concatenate_segments(self, segment_paths: List[str]) -> str:
        """
        Concatenate multiple video segments
        
        :param segment_paths: List of paths to video segments
        :return: Path to final compiled video
        """
        # Validate segments
        if not segment_paths:
            raise ValueError("No segments provided for concatenation")
        
        # Load video clips
        clips = [mp.VideoFileClip(path) for path in segment_paths]
        
        # Concatenate clips
        final_clip = mp.concatenate_videoclips(clips)
        
        # Output path
        output_filename = "compiled_video.mp4"
        output_path = os.path.join(self.output_folder, output_filename)
        
        # Write final video
        final_clip.write_videofile(output_path, logger=None)
        
        # Close clips
        for clip in clips:
            clip.close()
        final_clip.close()
        
        return output_path

    def process_segments(self, 
                         video_path: str, 
                         segments: List[Dict[str, float]]) -> str:
        """
        Process multiple video segments
        
        :param video_path: Path to source video
        :param segments: List of segment dictionaries with start and end times
        :return: Path to final compiled video
        """
        # Extract segments
        segment_paths = [
            self.extract_video_segment(video_path, seg['start'], seg['end'])
            for seg in segments
        ]
        
        # Concatenate segments
        return self.concatenate_segments(segment_paths)

def get_video_duration(video_path: str) -> float:
    """
    Get video duration using ffprobe
    
    :param video_path: Path to video file
    :return: Video duration in seconds
    """
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())