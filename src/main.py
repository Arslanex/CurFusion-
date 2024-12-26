import os
import sys
import difflib

from modules.youtube_downloader import YoutubeDownloader
from modules.audio_transcription import AudioTranscription
from modules.video_processing import VideoProcessor

# Import TranscriptManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.file_manager import TranscriptManager

PROJECT_FOLDER = '../projects/'
SEGMENTS_FOLDER = os.path.join(PROJECT_FOLDER, 'segments/')

# Ensure project and segments folders exist
os.makedirs(PROJECT_FOLDER, exist_ok=True)
os.makedirs(os.path.join(PROJECT_FOLDER, 'videos/'), exist_ok=True)
os.makedirs(os.path.join(PROJECT_FOLDER, 'audio/'), exist_ok=True)
os.makedirs(os.path.join(PROJECT_FOLDER, 'transcription/'), exist_ok=True)
os.makedirs(SEGMENTS_FOLDER, exist_ok=True)

youtube_downloader = YoutubeDownloader(download_path=PROJECT_FOLDER + 'videos/')
audio_transcription = AudioTranscription(output_path=PROJECT_FOLDER + 'transcription/', audio_path=PROJECT_FOLDER + 'audio/')
video_processor = VideoProcessor(upload_folder=PROJECT_FOLDER + 'videos/', output_folder=SEGMENTS_FOLDER)

# YouTube Video Download
youtube_links = input("Enter YouTube links (separated by space): ").split()
for link in youtube_links:
    youtube_downloader.download_video(link)
print("All videos downloaded")

# Audio Extraction and Transcription
audio_transcription.load_model()
video_files = [file for file in os.listdir(PROJECT_FOLDER + 'videos/') if os.path.isfile(os.path.join(PROJECT_FOLDER + 'videos/', file)) and file.endswith(".mp4")]
for video_file in video_files:
    audio_transcription.extract_audio(PROJECT_FOLDER + 'videos/' + video_file)

audio_files = [file for file in os.listdir(PROJECT_FOLDER + 'audio/') if os.path.isfile(os.path.join(PROJECT_FOLDER + 'audio/', file)) and file.endswith(".wav")]
for audio_file in audio_files:
    audio_transcription.transcribe_audio(PROJECT_FOLDER + 'audio/' + audio_file)

def find_word_matches(user_words, transcript_words, similarity_threshold=0.7):
    """
    Find matching words from transcripts for user input words.
    
    :param user_words: List of words from user input
    :param transcript_words: List of words from transcripts
    :param similarity_threshold: Minimum similarity score to consider a match
    :return: Dictionary of user words and their matches
    """
    word_matches = {}
    
    for user_word in user_words:
        # Find best matches for each user word
        matches = []
        for transcript_word in transcript_words:
            # Calculate similarity ratio
            similarity = difflib.SequenceMatcher(None, user_word.lower(), transcript_word.text.lower()).ratio()
            
            if similarity >= similarity_threshold:
                matches.append({
                    'word': transcript_word.text,
                    'similarity': similarity,
                    'start': transcript_word.start,
                    'end': transcript_word.end,
                    'source_file': transcript_word.source_file
                })
        
        # Sort matches by similarity (descending)
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        word_matches[user_word] = matches
    
    return word_matches

def main():
    # Initialize TranscriptManager
    transcript_manager = TranscriptManager(PROJECT_FOLDER)
    
    # Collect sentences grouped by file
    sentences_by_file = transcript_manager.collect_sentences()
    
    # Collect all words from transcripts
    all_transcript_words = transcript_manager.extract_word_details()
    
    # User input sentence
    print("\n🔍 Word Matching Tool")
    user_sentence = input("Enter a sentence to find matching words in transcripts: ")
    
    # Tokenize user sentence into words
    user_words = user_sentence.split()
    
    # Find matches for user words
    word_matches = find_word_matches(user_words, all_transcript_words)
    
    # Display matching results
    print("\n📊 Word Matching Results:")
    for user_word, matches in word_matches.items():
        print(f"\nUser Word: '{user_word}'")
        if matches:
            print("Top Matches:")
            for match in matches[:3]:  # Show top 3 matches
                print(f"  - '{match['word']}' (Similarity: {match['similarity']:.2%})")
                print(f"    File: {match['source_file']}")


if __name__ == "__main__":
    main()