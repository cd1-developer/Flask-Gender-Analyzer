from flask import Flask, render_template_string, request, send_file
import pandas as pd
import os
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# ===============================
# LOAD NAME LISTS
# ===============================
with open("Male_names.txt", "r", encoding="utf-8") as f:
    MALE_NAMES = {n.strip().lower() for n in f if n.strip()}
with open("Female_names.txt", "r", encoding="utf-8") as f:
    FEMALE_NAMES = {n.strip().lower() for n in f if n.strip()}
male_titles = {"mr", "sir", "gentleman", "king", "prince"}
female_titles = {"mrs", "ms", "miss", "madam", "queen", "princess"}
ignore_words = {"and","the","a","of","for","with","at","by","in","to","from","user","name"}
# ===============================
# CLEANING
# ===============================
def aggressively_clean_fullname(name):
    name = str(name).lower().strip()
    name = re.sub(r'\b(mr|mrs|ms|dr|prof|jr|sr|iii?|esq)\b', ' ', name)
    name = re.sub(r'[^a-z ]+', ' ', name)
    return re.sub(r'\s+', ' ', name).strip()
def clean_name(name):
    parts = [w for w in name.split() if len(w) > 1 and w not in ignore_words]
    return " ".join(parts)
# ===============================
# ANALYSIS
# ===============================
def analyze_name(name):
    clean_n = clean_name(name)
    if not clean_n:
        return "Unknown", 50
    words = clean_n.split()
    first = words[0]
    if any(w in male_titles for w in words):
        return "Male", 99
    if any(w in female_titles for w in words):
        return "Female", 99
    in_male = first in MALE_NAMES
    in_female = first in FEMALE_NAMES
    if in_male and not in_female:
        return "Male", 95
    if in_female and not in_male:
        return "Female", 95
    return "Unknown", 50
# ===============================
# WEB ROUTES
# ===============================
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>USA Gender Analyzer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        }
        body {
            background-color: #F8F9FA;
            color: #2C3E50;
            line-height: 1.6;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            padding: 40px;
            margin-top: 30px;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 1px solid #EAEAEA;
        }
        .header h1 {
            color: #1A1A1A;
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .header .subtitle {
            color: #666;
            font-size: 16px;
            font-weight: 400;
        }
        .upload-area {
            background: #F8F9FA;
            border: 2px dashed #DEE2E6;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            margin-bottom: 30px;
            transition: all 0.3s ease;
        }
        .upload-area:hover {
            border-color: #ADB5BD;
            background: #F1F3F5;
        }
        .upload-icon {
            font-size: 48px;
            color: #6C757D;
            margin-bottom: 20px;
        }
        .file-input {
            margin: 20px auto;
            display: block;
            padding: 12px;
            background: white;
            border: 1px solid #DEE2E6;
            border-radius: 6px;
            width: 100%;
            max-width: 400px;
            cursor: pointer;
        }
        .file-input:hover {
            border-color: #ADB5BD;
        }
        .submit-btn {
            background: #495057;
            color: white;
            border: none;
            padding: 14px 36px;
            font-size: 16px;
            font-weight: 500;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-top: 20px;
        }
        .submit-btn:hover {
            background: #343A40;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .download-section {
            text-align: center;
            margin-top: 30px;
            padding-top: 30px;
            border-top: 1px solid #EAEAEA;
        }
        .download-btn {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: #343A40;
            color: white;
            text-decoration: none;
            padding: 14px 28px;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .download-btn:hover {
            background: #212529;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .info-box {
            background: #F8F9FA;
            border-left: 4px solid #6C757D;
            padding: 20px;
            margin-top: 30px;
            border-radius: 0 6px 6px 0;
        }
        .info-box h3 {
            color: #495057;
            margin-bottom: 10px;
            font-size: 16px;
            font-weight: 600;
        }
        .info-box ul {
            color: #666;
            padding-left: 20px;
        }
        .info-box li {
            margin-bottom: 6px;
        }
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            .upload-area {
                padding: 30px 20px;
            }
            .header h1 {
                font-size: 24px;
            }
        }
        .success-message {
            color: #28A745;
            font-weight: 500;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>:bar_chart: USA Gender Analyzer</h1>
            <p class="subtitle">Strict analysis with no overlap – CSV & Excel files supported</p>
        </div>
        <form method="post" enctype="multipart/form-data">
            <div class="upload-area">
                <div class="upload-icon">:file_folder:</div>
                <h3>Upload Your File</h3>
                <p style="color: #666; margin: 10px 0 20px 0;">
                    Supports CSV or Excel files containing a "fullname" column
                </p>
                <input type="file" name="file" class="file-input" required>
                <button type="submit" class="submit-btn">Analyze & Process</button>
                {% if download %}
                <p class="success-message">✓ File processed successfully</p>
                {% endif %}
            </div>
        </form>
        {% if download %}
        <div class="download-section">
            <h3 style="margin-bottom: 20px; color: #495057;">Analysis Complete</h3>
            <a href="/download" class="download-btn">
                <span>:arrow_down:</span> Download Results
            </a>
        </div>
        {% endif %}
        <div class="info-box">
            <h3>How It Works</h3>
            <ul>
                <li>Upload files with a "fullname" column</li>
                <li>Names are cleaned and analyzed using strict USA name databases</li>
                <li>Returns gender classification with confidence percentage</li>
                <li>Results are saved to a new Excel file with all original data</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
processed_file = None
@app.route("/", methods=["GET","POST"])
def upload():
    global processed_file
    if request.method == "POST":
        file = request.files["file"]
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        if filename.endswith(".csv"):
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)
        df.columns = [c.lower() for c in df.columns]
        name_col = "fullname" if "fullname" in df.columns else "full_name"
        df["cleaned_fullname"] = df[name_col].apply(aggressively_clean_fullname)
        df[["Gender","Confidence_Raw"]] = df["cleaned_fullname"].apply(
            lambda x: pd.Series(analyze_name(x))
        )
        df["Confidence"] = df["Confidence_Raw"].astype(str) + "%"
        out = path.replace(".", "_USA_STRICT_NO_OVERLAP.")
        df.to_excel(out, index=False)
        processed_file = out
        return render_template_string(HTML, download=True)
    return render_template_string(HTML, download=False)

@app.route("/download")
def download():
    return send_file(processed_file, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)