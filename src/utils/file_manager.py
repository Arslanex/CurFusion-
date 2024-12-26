import os
import json
import glob
from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class WordDetail:
    """
    Dataclass representing detailed information about a single word in a transcript.
    
    Attributes:
        text (str): The word text
        start (float): Start time of the word
        end (float): End time of the word
        confidence (float): Confidence score of the word recognition
        source_file (str): Name of the source transcript file
        segment_index (int): Index of the segment containing the word
        word_index_in_segment (int): Position of the word within its segment
        segment_text (str): Full text of the segment containing the word
    """
    text: str
    start: float = 0.0
    end: float = 0.0
    confidence: float = 1.0
    source_file: str = ''
    segment_index: int = 0
    word_index_in_segment: int = 0
    segment_text: str = ''

    @property
    def duration(self) -> float:
        """Calculate the duration of the word."""
        return self.end - self.start

@dataclass
class SentenceDetail:
    """
    Dataclass representing detailed information about a single sentence in a transcript.
    
    Attributes:
        text (str): The sentence text
        start (float): Start time of the sentence
        end (float): End time of the sentence
        source_file (str): Name of the source transcript file
        words (List[WordDetail]): List of words in the sentence
    """
    text: str
    start: float = 0.0
    end: float = 0.0
    source_file: str = ''
    words: List[WordDetail] = field(default_factory=list)

class TranscriptManager:
    def __init__(self, project_dir):
        """
        Initialize TranscriptManager with project directory.
        
        :param project_dir: Root directory of the project
        """
        self.project_dir = project_dir
        self.transcript_dir = os.path.join(project_dir, 'transcription/')
        
        # Ensure transcript directory exists
        os.makedirs(self.transcript_dir, exist_ok=True)

    def find_transcript_files(self):
        """
        Find all JSON transcript files in the transcription directory.
        
        :return: List of full paths to JSON transcript files
        """
        return glob.glob(os.path.join(self.transcript_dir, '*.json'))

    def _parse_transcript_file(self, transcript_file):
        """
        Parse a single transcript file with flexible JSON structure.
        
        :param transcript_file: Path to the JSON transcript file
        :return: Parsed transcript data
        """
        with open(transcript_file, 'r', encoding='utf-8') as f:
            try:
                transcript_data = json.load(f)
                return transcript_data
            except json.JSONDecodeError:
                print(f"Error decoding JSON in {transcript_file}")
                return None

    def collect_sentences(self) -> Dict[str, List[SentenceDetail]]:
        """
        Collect sentence data from all transcript files, grouped by source file.
        
        :return: Dictionary with source filenames as keys and lists of SentenceDetail objects as values
        """
        sentences_by_file: Dict[str, List[SentenceDetail]] = {}
        
        for transcript_file in self.find_transcript_files():
            transcript_data = self._parse_transcript_file(transcript_file)
            if not transcript_data or 'segments' not in transcript_data:
                continue

            # Use basename as the key to group sentences
            file_key = os.path.splitext(os.path.basename(transcript_file))[0] + '.mp4'
            sentences_by_file[file_key] = []

            for segment_index, segment in enumerate(transcript_data['segments']):
                # Create WordDetail objects for each word in the segment
                words = [
                    WordDetail(
                        text=word.get('word', '').strip(),
                        start=word.get('start', 0),
                        end=word.get('end', 0),
                        confidence=word.get('confidence', 1.0),
                        source_file=file_key,
                        segment_index=segment_index,
                        word_index_in_segment=word_idx,
                        segment_text=segment.get('text', '')
                    )
                    for word_idx, word in enumerate(segment.get('words', []))
                ]

                sentence = SentenceDetail(
                    text=segment.get('text', '').strip(),
                    start=segment.get('start', 0),
                    end=segment.get('end', 0),
                    source_file=file_key,
                    words=words
                )
                sentences_by_file[file_key].append(sentence)
            
            # Sort sentences within each file by start time
            sentences_by_file[file_key] = sorted(
                sentences_by_file[file_key], 
                key=lambda x: x.start
            )
        
        return sentences_by_file

    def extract_word_details(self) -> List[WordDetail]:
        """
        Extract detailed word-level information from all transcript files.
        
        :return: List of WordDetail objects
        """
        all_word_details = []
        for transcript_file in self.find_transcript_files():
            transcript_data = self._parse_transcript_file(transcript_file)
            file_key = os.path.splitext(os.path.basename(transcript_file))[0] + '.mp4'
            if not transcript_data or 'segments' not in transcript_data:
                continue

            for segment_index, segment in enumerate(transcript_data['segments']):
                words = [
                    WordDetail(
                        text=word.get('word', '').strip(),
                        start=word.get('start', 0),
                        end=word.get('end', 0),
                        confidence=word.get('confidence', 1.0),
                        source_file=file_key,
                        segment_index=segment_index,
                        word_index_in_segment=word_idx,
                        segment_text=segment.get('text', '')
                    )
                    for word_idx, word in enumerate(segment.get('words', []))
                ]
                all_word_details.extend(words)
        
        return sorted(all_word_details, key=lambda x: x.start)

    def search_transcripts(self, query, search_type='sentence'):
        """
        Search through transcripts for a specific query.
        
        :param query: Search term
        :param search_type: 'sentence' or 'word'
        :return: List of matching transcript entries
        """
        query = query.lower()
        
        if search_type == 'sentence':
            entries = self.collect_sentences()
            return [
                sentence for sentences in entries.values() for sentence in sentences 
                if query in sentence.text.lower()
            ]
        elif search_type == 'word':
            entries = self.extract_word_details()
            return [
                word for word in entries 
                if query in word.text.lower()
            ]
        else:
            raise ValueError("search_type must be 'sentence' or 'word'")

    def collect_words(self):
        """
        Collect word-level data from all transcript files.
        
        :return: List of dictionaries containing word information
        """
        all_words = []
        for transcript_file in self.find_transcript_files():
            transcript_data = self._parse_transcript_file(transcript_file)
            if not transcript_data:
                continue

            # Try multiple parsing strategies
            if 'segments' in transcript_data:
                # Whisper-style transcript
                for segment in transcript_data['segments']:
                    for word in segment.get('words', []):
                        word_info = {
                            'text': word.get('word', '').strip(),
                            'start': word.get('start', 0),
                            'end': word.get('end', 0),
                            'source_file': os.path.basename(transcript_file)
                        }
                        all_words.append(word_info)
            else:
                # Fallback parsing
                text = transcript_data.get('text', '')
                words = text.split()
                for word in words:
                    word_info = {
                        'text': word.strip(),
                        'start': 0,
                        'end': 0,
                        'source_file': os.path.basename(transcript_file)
                    }
                    all_words.append(word_info)
        
        return sorted(all_words, key=lambda x: x['start'])

    def export_summary(self, output_path=None):
        """
        Export a summary of all transcripts.
        
        :param output_path: Path to save the summary. If None, saves in transcript directory.
        :return: Path to the exported summary file
        """
        if output_path is None:
            output_path = os.path.join(self.transcript_dir, 'transcript_summary.json')
        
        summary = {
            'total_transcripts': len(self.find_transcript_files()),
            'sentences': self.collect_sentences(),
            'words': self.collect_words()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return output_path

# Example usage in main block
if __name__ == "__main__":
    project_dir = 'projects/'  # Adjust as needed
    transcript_manager = TranscriptManager(project_dir)
    
    # Collect sentences grouped by file
    sentences_by_file = transcript_manager.collect_sentences()
    
    # Detailed analysis of sentences by file
    print("Transcript Sentences Analysis:")
    for filename, sentences in sentences_by_file.items():
        print(f"\nFile: {filename}")
        print(f"Total Sentences: {len(sentences)}")
        
        # Sentence-level statistics
        sentence_durations = [sentence.end - sentence.start for sentence in sentences]
        total_file_duration = sum(sentence_durations)
        
        print(f"Total File Duration: {total_file_duration:.2f} seconds")
        print(f"Average Sentence Duration: {sum(sentence_durations)/len(sentences):.2f} seconds")
        
        # Word-level statistics
        total_words = sum(len(sentence.words) for sentence in sentences)
        print(f"Total Words: {total_words}")
        
        # Optional: Print first few sentences
        print("\nFirst 3 Sentences:")
        for sentence in sentences[:3]:
            print(f"- {sentence.text}")
            print(f"  Start: {sentence.start:.2f}, End: {sentence.end:.2f}")
            print(f"  Words: {len(sentence.words)}")