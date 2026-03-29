"""Module to define app routes"""
from datetime import datetime
import os
import logging
import uuid
import numpy as np
from flask import Blueprint, render_template, request, flash, jsonify, current_app
from scipy.io import wavfile
from scipy.signal import resample
from .output_table import output_table
from .parse_files import parse_files
from .word_analysis import word_analysis
from .utils.security import sanitize_filename
from .utils.validators import validate_document_upload, validate_media_upload, ValidationError

main = Blueprint('main', __name__)


@main.route('/')
def index():
    """Render the home page."""
    return render_template('pages/modern_home.html')


@main.route("/storm/word", methods=["GET"])
def upload_word():
    """Render the word file uploading page."""
    return render_template('pages/modern_word_upload.html')


@main.route("/storm/word/results", methods=["POST"])
def analyze_word():
    """Analyze Word documents and generate acronym sweep output.

    This route handles Word document uploads, performs acronym sweep analysis,
    and generates output files (Word, Excel, HTML) based on the analysis.

    Returns:
        Rendered word result page with links to generated output files.
    """
    upload_dir = os.path.join("src", 'static', "uploads")
    output_dir = os.path.join("src", "static", "outputs")
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    file_path = None
    acronym_filepath = None
    output_html = None

    try:
        # Validate file uploads
        file = request.files.get('file')
        acronym_file = request.files.get('excel')

        if not file or not file.filename:
            flash('No Word document provided', 'error')
            return render_template('pages/word_result.html', findings={}, output_html='', output_filenames={})

        if not acronym_file or not acronym_file.filename:
            flash('No acronym Excel file provided', 'error')
            return render_template('pages/word_result.html', findings={}, output_html='', output_filenames={})

        # Validate document files
        try:
            validate_document_upload(file)
            validate_document_upload(acronym_file)
        except ValidationError as ve:
            flash(str(ve), 'error')
            return render_template('pages/word_result.html', findings={}, output_html='', output_filenames={})

        # Sanitize filenames to prevent path traversal
        safe_filename = sanitize_filename(file.filename)
        safe_acronym_filename = sanitize_filename(acronym_file.filename)

        if not safe_filename or not safe_acronym_filename:
            flash('Invalid filename provided', 'error')
            return render_template('pages/word_result.html', findings={}, output_html='', output_filenames={})

        # Save uploaded files with sanitized names
        file_path = os.path.join(upload_dir, safe_filename)
        acronym_filepath = os.path.join(upload_dir, safe_acronym_filename)

        file.save(file_path)
        acronym_file.save(acronym_filepath)

        current_app.logger.info(f"Processing file: {safe_filename}")

        # Parse and analyze documents
        parser = parse_files.Parser()
        doc = parser.read_word_file(os.path.abspath(file_path))
        acronyms = parser.read_excel_file(acronym_filepath)
        doc, findings = word_analysis.WordAnalyzer().acronym_sweep(doc, acronyms)

        current_app.logger.info(f"Analysis complete. Findings count: {len(findings)}")

        # Generate output filenames (sanitized)
        base_name = os.path.splitext(safe_filename)[0]
        output_filenames = {
            'word': f"acronym_swept_{base_name}.docx",
            'excel': f"acronym_sweep_findings_{base_name}.xlsx",
            'html': f"output_acronym_sweep_{base_name}.html"
        }

        # Write output files
        we = output_table.WriteExcel()
        output_file = os.path.join(output_dir, output_filenames['word'])
        we.save_doc(doc, output_file)

        output_excel = os.path.join(output_dir, output_filenames['excel'])
        we.write_excel_acronym_sweep(findings, output_excel)

        output_html = os.path.join(output_dir, output_filenames['html'])
        we.excel_to_html(output_excel, output_html)

        # Read HTML for display (will be sanitized in parse_files)
        html_content = parser.read_html(output_html)

        return render_template('pages/modern_word_result.html', findings=findings,
                               output_html=html_content, output_filenames=output_filenames)

    except Exception as e:
        # Log the full error server-side, but show generic message to user
        current_app.logger.error(f"Error processing Word document: {str(e)}", exc_info=True)
        flash('An error occurred while processing the document. Please try again.', 'error')
        return render_template('pages/word_result.html', findings={}, output_html='', output_filenames={})

    finally:
        # Cleanup uploaded files after processing (keep outputs)
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if acronym_filepath and os.path.exists(acronym_filepath):
                os.remove(acronym_filepath)
        except Exception as cleanup_error:
            current_app.logger.warning(f"Failed to cleanup uploaded files: {cleanup_error}")


@main.route('/storm/cleanup', methods=["GET"])
def cleanup_static_files():
    """Route to clear old static files based on modification time"""
    output_dir = os.path.join("src", "static", "outputs")
    cleaned_files = []

    try:
        if not os.path.exists(output_dir):
            return jsonify({"message": "Output directory does not exist", "cleaned_files": []})

        current_time = datetime.now().timestamp()
        max_age_seconds = 24 * 60 * 60  # 24 hours

        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)

            # Skip directories
            if os.path.isdir(file_path):
                continue

            try:
                # Check file age based on modification time
                file_mtime = os.path.getmtime(file_path)
                file_age = current_time - file_mtime

                if file_age > max_age_seconds:
                    os.remove(file_path)
                    cleaned_files.append(filename)
                    current_app.logger.info(f"Cleaned up old file: {filename}")

            except Exception as file_error:
                current_app.logger.warning(f"Failed to process file {filename}: {file_error}")
                continue

        return jsonify({
            "message": f"Cleanup completed. Removed {len(cleaned_files)} file(s).",
            "cleaned_files": cleaned_files
        })

    except Exception as e:
        current_app.logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to cleanup files"}), 500


@main.route('/record', methods=["GET"])
def record():
    """
    Render the page where users can record or upload a video.

    Returns:
        Response: A rendered HTML page for video recording.
    """
    return render_template('pages/modern_record.html')


@main.route('/video-upload', methods=['POST'])
def video_upload():
    """
    Handle the video file upload, save it to the server, and return a response.

    This endpoint accepts a video file via a POST request and saves it in the
    'static/outputs' folder. If the upload is successful, it returns the filename
    of the saved video.

    Returns:
        Response: A JSON response with a success message and the video filename
                  or an error message if no file is received.
    """
    output_folder = os.path.join("src", "static", "outputs")
    os.makedirs(output_folder, exist_ok=True)

    video = request.files.get('video')
    if not video:
        return jsonify({'error': 'No video file received'}), 400

    try:
        # Validate media file
        validate_media_upload(video, '.webm')
    except ValidationError as ve:
        return jsonify({'error': str(ve)}), 400

    # Generate secure filename
    filename = f"{uuid.uuid4()}.webm"
    save_path = os.path.join(output_folder, filename)

    try:
        video.save(save_path)
        current_app.logger.info(f"Video saved: {filename}")
        return jsonify({'message': 'Video saved', 'filename': filename})
    except Exception as e:
        current_app.logger.error(f"Error saving video: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to save video file'}), 500


@main.route('/audio-upload', methods=['POST'])
def audio_upload():
    """
    Handle the audio file upload, process it, and return the transcription.

    This endpoint accepts an audio file, processes it (including resampling and
    normalization), and then uses the Whisper model to transcribe the audio. The
    processed audio is saved to the server, and the transcription result is returned.

    Returns:
        Response: A JSON response containing the transcription of the audio
                  or an error message if the file is not valid or an exception occurs.
    """
    output_folder = os.path.join("src", "static", "outputs")
    os.makedirs(output_folder, exist_ok=True)

    audio = request.files.get('audio')
    if not audio:
        return jsonify({'error': 'No audio file received'}), 400

    try:
        # Validate media file
        validate_media_upload(audio, '.wav')
    except ValidationError as ve:
        return jsonify({'error': str(ve)}), 400

    filename = f"{uuid.uuid4()}.wav"
    save_path = os.path.join(output_folder, filename)

    try:
        audio.save(save_path)

        # Read and process audio
        sample_rate, data = wavfile.read(save_path)

        # Convert stereo to mono
        if len(data.shape) == 2:
            data = data.mean(axis=1)
            max_val = np.max(np.abs(data))
            if max_val > 0:
                data = data / max_val

        # Normalize data types to float32
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
        elif data.dtype == np.uint8:
            data = (data.astype(np.float32) - 128) / 128.0
        elif data.dtype == np.float64:
            data = data.astype(np.float32)
        elif data.dtype != np.float32:
            return jsonify({'error': f'Unsupported sample type: {data.dtype}'}), 400

        # Resample to 16kHz (Whisper's expected sample rate)
        target_sr = 16000
        if sample_rate != target_sr:
            new_len = int(len(data) * target_sr / sample_rate)
            data = resample(data, new_len)
            sample_rate = target_sr

        # Use pre-loaded Whisper model from app context
        model = current_app.whisper_model
        if model is None:
            current_app.logger.error("Whisper model not loaded")
            return jsonify({"error": "Transcription service unavailable"}), 503

        # Save processed audio
        output_path = os.path.join(output_folder, f"processed_{filename}")
        wavfile.write(output_path, sample_rate, np.int16(data * 32767))

        # Transcribe
        result = model.transcribe(audio=data, language='en', fp16=False)

        current_app.logger.info(f"Audio transcribed successfully: {filename}")
        return jsonify({"transcription": result["text"], "segments": result["segments"]})

    except Exception as e:
        current_app.logger.error(f"Error processing audio: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to process audio file"}), 500

    finally:
        # Cleanup temporary audio file
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
        except Exception as cleanup_error:
            current_app.logger.warning(f"Failed to cleanup audio file: {cleanup_error}")
