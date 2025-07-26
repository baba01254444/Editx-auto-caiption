from flask import Flask, render_template, request, send_file
import whisper
import os
import uuid
from werkzeug.utils import secure_filename
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

model = whisper.load_model("base")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "video" not in request.files:
            return "No file uploaded", 400
        file = request.files["video"]
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{filename}")
        file.save(file_path)

        # Run Whisper
        result = model.transcribe(file_path)
        srt_path = file_path + ".srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            for segment in result["segments"]:
                f.write(f"{segment['id']+1}\n")
                f.write(f"{format_time(segment['start'])} --> {format_time(segment['end'])}\n")
                f.write(f"{segment['text'].strip()}\n\n")

        # Burn subtitles using ffmpeg
        output_path = os.path.join(OUTPUT_FOLDER, f"captioned_{uuid.uuid4()}.mp4")
        subprocess.call([
            "ffmpeg", "-i", file_path, "-vf", f"subtitles={srt_path}",
            "-c:a", "copy", output_path
        ])

        return send_file(output_path, as_attachment=True)

    return render_template("index.html")

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:06.3f}".replace(".", ",")

if __name__ == "__main__":
    app.run(debug=True)
