import os
import json
import subprocess
from whisper import load_model

class AudioTranscription:
    def __init__(self, audio_path=None, output_path=None, model_name='base'):
        if output_path is None:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            output_path = os.path.join(root_dir, "transcripts")

        self.output_path = output_path
        os.makedirs(self.output_path, exist_ok=True)

        if audio_path is None:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            audio_path = os.path.join(root_dir, "audio")

        self.audio_path = audio_path
        os.makedirs(self.audio_path, exist_ok=True)

        self.model_name = model_name
        self.model = None

    def load_model(self):
        """Load the  model."""
        print("Loading model: %s", self.model_name)
        try:
            self.model = load_model(self.model_name)
            print("Model '%s' loaded successfully.", self.model_name)
        except Exception as e:
            print("Failed to load model '%s': %s", self.model_name, str(e))
            raise RuntimeError(f"Model loading failed: {e}")

    def extract_audio(self, video_path):
        if not os.path.exists(video_path):
            print(f"[ERROR] Video file not found: {video_path}")
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not video_path.lower().endswith(".mp4"):
            print(f"[ERROR] Unsupported video format: {video_path}")
            raise ValueError("Unsupported video format. Please provide an .mp4 file.")

        audio_path = os.path.join(
            self.audio_path,
            os.path.basename(video_path).replace(".mp4", ".wav")
        )

        if os.path.exists(audio_path):
            print(f"[WARNING] Audio file already exists: {audio_path}. It will be overwritten.")

        try:
            print(f"[INFO] Extracting audio from video: {video_path}")
            subprocess.run([
                "ffmpeg",
                "-i", video_path,
                "-vn",  # Disable video
                "-acodec", "pcm_s16le",  # 16-bit PCM
                "-ar", "16000",  # 16kHz sample rate
                "-ac", "1",  # Mono channel
                audio_path
            ], check=True, capture_output=True, text=True)

            # Verify audio file was created
            if not os.path.exists(audio_path):
                raise FileExistsError("Audio extraction failed: Output file not created")

            print(f"[SUCCESS] Audio extraction complete: {audio_path}")
            return audio_path


        except subprocess.CalledProcessError as e:
            print(f"[ERROR] FFmpeg audio extraction failed: {e}")
            print(f"[ERROR] FFmpeg stdout: {e.stdout}")
            print(f"[ERROR] FFmpeg stderr: {e.stderr}")
            raise SystemError(f"Audio extraction failed: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error during audio extraction: {e}")
            raise SystemError(f"Audio extraction failed: {e}")

    def transcribe_audio(self, audio_path):
        if not os.path.exists(audio_path):
            print("Audio file not found: %s", audio_path)
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if not self.model:
            print(" model is not loaded.")
            raise ImportError(" moodel is not loaded. Call 'load_model()' first.")

        try:
            result = self.model.transcribe(audio_path, word_timestamps=True)
            transcript_path = os.path.join(
                self.output_path,
                os.path.basename(audio_path).replace(".wav", ".json")
            )

            with open(transcript_path, "w") as f:
                json.dump(result, f, indent=4)

        except Exception as e:
            print("Error during transcription: %s", str(e))
            raise SystemError(f"Transcription failed: {e}")


if __name__ == "__main__":
    print(f'Path to the video file to process')
    video_path = '../../downloads/'+input('> ')

    try:
        module = AudioTranscription()
        module.load_model()

        print("Starting audio extraction...")
        audio_path = module.extract_audio(video_path)

        print("Starting transcription...")
        transcript_path = module.transcribe_audio(audio_path)

        print("Transcription process completed. Transcript saved at: %s", transcript_path)
    except Exception as e:
        print("Process failed: %s", str(e))
