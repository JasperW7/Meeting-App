from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pydub import AudioSegment
import assemblyai as aai
import os
import traceback
import tempfile
import openai as gpt

aai.settings.api_key = "aa6858980b8a4fda9103de2e70acc2cd"
app = Flask(__name__)
CORS(app)
@app.route("/")
def home():
    return render_template("home.html")
@app.route("/record")
def record():
    return render_template("record.html")
@app.route("/upload", methods = ["GET","POST"])
def upload_page():
    if request.method == "GET": 
        return render_template("upload.html")


@app.route("/transcribe/", methods=["POST"])
def transcribe():
    try:
        file = request.files["audio"]
        raw_path = "temp.webm"
        wav_path = "output.wav"

        file.save(raw_path)

        audio = AudioSegment.from_file(raw_path, format="webm")
        audio.export(wav_path, format="wav")

        transcriber = aai.Transcriber()
        config = aai.TranscriptionConfig(summarization=True)
        transcript = transcriber.transcribe(wav_path)
        summary = transcript.summary

        os.remove(raw_path)
        os.remove(wav_path)

        return jsonify({"text": transcript.text, 
                        "summary": summary if summary else "No summary available."})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
    
@app.route("/upload/", methods=["POST"])
def upload():
    try:
        file = request.files["video"]
        filename = file.filename.lower()

        if not (filename.endswith(".mp4") or filename.endswith(".mp3")):
            return jsonify({"error": "Only MP4 or MP3 files are accepted."}), 400

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, filename)
            mp3_path = os.path.join(temp_dir, "audio.mp3")

            file.save(input_path)

            if filename.endswith(".mp4"):
                video = AudioSegment.from_file(input_path, format="mp4")
                video.export(mp3_path, format="mp3")
            else:
                os.rename(input_path, mp3_path)

            transcriber = aai.Transcriber()
            config = aai.TranscriptionConfig(summarization=True)
            transcript = transcriber.transcribe(mp3_path)
            summary = transcript.summary
            # summary = gpt_summary(transcript.text)

            return jsonify({
                "text": transcript.text,
                "summary": summary if summary else "No summary available."
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# def gpt_summary(transcript_text):
#     prompt = (
#         "Convert the following transcript into detailed bullet-point jot notes: "
#         "Keep the notes concise, clear, and structured while maintaining important facts, details and ideas."
#         f"{transcript_text}"
#     )
#     response = gpt.ChatCompletion.create(
#         model = "gpt-3.5-turbo",
#         messages = [{"role": "system", "content": "You are a professional meeting note-taker."},
#             {"role": "user", "content": prompt}
#             ],
#         temperature = 0.3,
#         max_tokens = 800
#     )
#     return response.choices[0].message.content.strip()
if __name__ == "__main__":
    app.run(debug=True)
