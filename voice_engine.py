from app_config import get_sarvam_api_key
import os
import re
import tempfile
import wave

from sarvamai import SarvamAI
from sarvamai.play import save


# =========================================================
# SARVAM CLIENT
# =========================================================

def get_client():

    api_key = get_sarvam_api_key()

    if not api_key:
        raise RuntimeError(
            "SARVAM_API_KEY is not set."
        )

    return SarvamAI(
        api_subscription_key=api_key
    )


# =========================================================
# SPEECH TO TEXT — SAARAS V4
# =========================================================

def transcribe_audio(
    audio_bytes,
    language="English"
):

    client = get_client()

    # -----------------------------------------------------
    # Determine language configuration
    # -----------------------------------------------------

    if language == "Tamil":

        language_code = "ta-IN"
        mode = "transcribe"

    elif language == "English":

        language_code = "en-IN"
        mode = "transcribe"

    else:

        # English + Tamil
        language_code = "unknown"
        mode = "codemix"


    # -----------------------------------------------------
    # Create temporary WAV file
    # -----------------------------------------------------

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as temp_file:

            temp_file.write(audio_bytes)
            temp_path = temp_file.name


        # -------------------------------------------------
        # Saaras v4
        # -------------------------------------------------

        response = client.speech_to_text.transcribe(
            file=open(temp_path, "rb"),
            model="saaras:v4",
            mode=mode,
            language_code=language_code
        )

        return {
            "transcript": response.transcript,
            "language_code": response.language_code
        }

    finally:

        if temp_path:

            try:
                os.remove(temp_path)

            except OSError:
                pass




# Sarvam Bulbul v3 accepts at most 2,500 characters per request.
# Keep a safety margin below the API limit.
TTS_CHUNK_LIMIT = 2000


def split_text_for_tts(text, max_chars=TTS_CHUNK_LIMIT):
    """Split text into chunks that fit the TTS API limit."""
    text = re.sub(r"[\\*_#`]", "", str(text or ""))
    text = text.replace("•", " ").strip()

    if not text:
        raise ValueError("There is no text available to convert to speech.")

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining.strip())
            break

        # Prefer paragraph/sentence boundaries.
        candidates = [
            remaining.rfind("\\n", 0, max_chars),
            remaining.rfind(". ", 0, max_chars),
            remaining.rfind("? ", 0, max_chars),
            remaining.rfind("! ", 0, max_chars),
            remaining.rfind("; ", 0, max_chars),
        ]
        boundary = max(candidates)

        # Otherwise split at a word boundary.
        if boundary < max_chars // 2:
            boundary = remaining.rfind(" ", 0, max_chars)

        # Last resort for a very long unbroken token.
        if boundary <= 0:
            boundary = max_chars
        elif remaining[boundary:boundary + 1] in ".?!;":
            boundary += 1

        chunk = remaining[:boundary].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[boundary:].strip()

    return chunks


def combine_wav_files(input_paths, output_path):
    """Combine compatible WAV chunks into one WAV file."""
    with wave.open(input_paths[0], "rb") as first:
        params = first.getparams()
        frame_data = [first.readframes(first.getnframes())]

    for path in input_paths[1:]:
        with wave.open(path, "rb") as part:
            current = part.getparams()
            if (
                current.nchannels != params.nchannels
                or current.sampwidth != params.sampwidth
                or current.framerate != params.framerate
                or current.comptype != params.comptype
            ):
                raise RuntimeError(
                    "Sarvam returned incompatible WAV audio chunks; "
                    "the chunks cannot be safely combined."
                )
            frame_data.append(part.readframes(part.getnframes()))

    with wave.open(output_path, "wb") as output:
        output.setparams(params)
        for frames in frame_data:
            output.writeframes(frames)

# =========================================================
# TEXT TO SPEECH — BULBUL V3
# =========================================================

def generate_speech(text, language="English"):
    client = get_client()

    if language == "Tamil":
        language_code = "ta-IN"
        speaker = "priya"
    elif language == "English + Tamil":
        # Preserve the existing language choice for mixed-language answers.
        language_code = "ta-IN"
        speaker = "priya"
    else:
        language_code = "en-IN"
        speaker = "priya"

    chunks = split_text_for_tts(text)

    # Keep the simple one-request path for short answers.
    if len(chunks) == 1:
        audio = client.text_to_speech.convert(
            text=chunks[0],
            language_code=language_code,
            model="bulbul:v3",
            speaker=speaker,
            pace=1.0
        )

        output_path = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ).name

        try:
            save(audio, output_path)
            return output_path
        except Exception:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise

    # Generate each chunk separately, then combine the WAV audio in order.
    chunk_paths = []
    output_path = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    ).name

    try:
        for chunk in chunks:
            audio = client.text_to_speech.convert(
                text=chunk,
                language_code=language_code,
                model="bulbul:v3",
                speaker=speaker,
                pace=1.0
            )

            chunk_path = tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            ).name
            chunk_paths.append(chunk_path)
            save(audio, chunk_path)

        combine_wav_files(chunk_paths, output_path)
        return output_path

    except Exception:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise

    finally:
        for chunk_path in chunk_paths:
            try:
                os.remove(chunk_path)
            except OSError:
                pass