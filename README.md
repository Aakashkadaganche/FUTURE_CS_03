Secure File Sharing System
A secure file sharing web application built with Python Flask that allows users to upload and download files safely using AES-256 encryption.
This project focuses on security, encryption, and file integrity, simulating real-world scenarios in healthcare, legal, and corporate environments.
________________________________________
Key Features
•	Secure file upload and download functionality
•	AES-256 encryption for all files at rest
•	Basic encryption key management
•	File integrity verification using SHA-256 hashes
•	User-friendly interface for file management
•	Delete files securely
•	Well-documented code and security considerations
________________________________________
Technologies Used
•	Python 3.10+
•	Flask (Backend)
•	PyCryptodome (AES encryption)
•	HTML/CSS/Bootstrap (Frontend)
•	UUID & SHA-256 for file tracking and integrity
•	Git & GitHub for version control
________________________________________
Setup Instructions
1.Clone the repository:
git clone https://github.com/your-username/Secure_File_Sharing_System.git
cd Secure_File_Sharing_System

2.Create a virtual environment and install dependencies:
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / Mac
source venv/bin/activate

pip install -r requirements.txt

3.Run the Flask app:
python app.py
Open your browser at: http://127.0.0.1:5000
________________________________________
Folder Structure  
Secure_File_Sharing_System/
├─ app.py
├─ README.md
├─ SECURITY.md
├─ requirements.txt
├─ .gitignore
├─ uploads/           # stores encrypted files (auto-generated)
├─ templates/
│   └─ index.html
└─ static/
    └─ css/
        └─ style.css
________________________________________
Usage
•	Upload files: Use the "Choose File" button to upload files.
•	Download files: Click the "Download" button to retrieve files.
•	Delete files: Click the "Delete" button to remove files securely.
All files are encrypted at rest and verified for integrity during download.

