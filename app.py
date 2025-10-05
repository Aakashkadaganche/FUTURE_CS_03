from flask import Flask, request, render_template, send_file, redirect, url_for, flash
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from io import BytesIO
import hashlib
import json
import uuid
import time
import tempfile
from datetime import datetime

# -------------------------------
# AES key management
# -------------------------------
ENV_FILE = '.env'
METADATA_FILE = os.path.join('uploads', 'metadata.json')

def create_aes_key():
    key = get_random_bytes(32)  # 256-bit AES key
    with open(ENV_FILE, 'w') as f:
        f.write(f"ENCRYPTION_KEY={key.hex()}\n")
    print(f".env created with ENCRYPTION_KEY: {key.hex()}")
    return key

if not os.path.exists(ENV_FILE):
    ENCRYPTION_KEY = create_aes_key()
else:
    load_dotenv()
    try:
        ENCRYPTION_KEY = bytes.fromhex(os.getenv('ENCRYPTION_KEY'))
    except Exception:
        print("Invalid AES key in .env. Regenerating...")
        ENCRYPTION_KEY = create_aes_key()

# -------------------------------
# Flask setup
# -------------------------------
app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure metadata file exists
if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, 'w') as f:
        json.dump({}, f)

# -------------------------------
# Template filter for timestamp
# -------------------------------
@app.template_filter('datetimeformat')
def datetimeformat(value):
    try:
        return datetime.fromtimestamp(int(value)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return value

# -------------------------------
# Helper functions
# -------------------------------
def encrypt_file(data):
    iv = get_random_bytes(16)
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(data, AES.block_size))
    return iv + ciphertext

def decrypt_file(data):
    iv = data[:16]
    ciphertext = data[16:]
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), AES.block_size)

def hash_file(data):
    return hashlib.sha256(data).hexdigest()

def load_metadata():
    with open(METADATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_metadata(meta):
    fd, tmp = tempfile.mkstemp(dir=UPLOAD_FOLDER)
    with os.fdopen(fd, 'w') as f:
        json.dump(meta, f, indent=2)
    os.replace(tmp, METADATA_FILE)

# -------------------------------
# Routes
# -------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded = request.files.get('file')
        if uploaded:
            original_name = secure_filename(uploaded.filename)
            data = uploaded.read()

            encrypted_data = encrypt_file(data)
            uid = uuid.uuid4().hex
            stored_filename = f"{uid}.enc"
            filepath = os.path.join(UPLOAD_FOLDER, stored_filename)

            fd, tmp_path = tempfile.mkstemp(dir=UPLOAD_FOLDER)
            try:
                with os.fdopen(fd, 'wb') as tmpf:
                    tmpf.write(encrypted_data)
                os.replace(tmp_path, filepath)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            file_hash = hash_file(data)
            meta = load_metadata()
            meta[stored_filename] = {
                "original_filename": original_name,
                "hash": file_hash,
                "timestamp": int(time.time())
            }
            save_metadata(meta)

            flash(f"File '{original_name}' uploaded successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash("No file selected.", "danger")

    meta = load_metadata()
    files = []
    sorted_items = sorted(meta.items(), key=lambda kv: kv[1].get('timestamp', 0), reverse=True)
    for stored_name, info in sorted_items:
        if os.path.exists(os.path.join(UPLOAD_FOLDER, stored_name)):
            files.append({
                "stored_name": stored_name,
                "original_filename": info.get("original_filename", stored_name.replace('.enc','')),
                "timestamp": info.get("timestamp")
            })
    return render_template('index.html', files=files)

@app.route('/download/<stored_filename>')
def download(stored_filename):
    stored_filename = secure_filename(stored_filename)
    filepath = os.path.join(UPLOAD_FOLDER, stored_filename)
    meta = load_metadata()
    info = meta.get(stored_filename)

    if not os.path.exists(filepath):
        flash("File not found on disk.", "danger")
        return redirect(url_for('index'))
    if not info:
        flash("File metadata missing.", "danger")
        return redirect(url_for('index'))

    try:
        with open(filepath, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = decrypt_file(encrypted_data)
    except Exception:
        flash("Error reading or decrypting file.", "danger")
        return redirect(url_for('index'))

    original_hash = info.get("hash")
    if not original_hash or hash_file(decrypted_data) != original_hash:
        flash("File integrity check failed!", "danger")
        return redirect(url_for('index'))

    return send_file(
        BytesIO(decrypted_data),
        download_name=info.get("original_filename", stored_filename.replace('.enc','')),
        as_attachment=True
    )

@app.route('/delete/<stored_filename>', methods=['POST'])
def delete(stored_filename):
    stored_filename = secure_filename(stored_filename)
    filepath = os.path.join(UPLOAD_FOLDER, stored_filename)
    meta = load_metadata()

    if stored_filename in meta:
        meta.pop(stored_filename)
        save_metadata(meta)

    if os.path.exists(filepath):
        os.remove(filepath)
        flash("File deleted successfully!", "success")
    else:
        flash("File not found on disk.", "danger")

    return redirect(url_for('index'))

# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)
