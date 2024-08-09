from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message
from transformers import pipeline
import datetime
import os
from werkzeug.utils import secure_filename
import PyPDF2

app = Flask(__name__)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.example.com'  # Replace with your SMTP server
app.config['MAIL_PORT'] = 587  # Replace with your SMTP port
app.config['MAIL_USERNAME'] = 'your-email@example.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your-email-password'  # Replace with your email password
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# Configure file upload
UPLOAD_FOLDER = 'uploaded_pdfs'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize the summarization model
summarizer = pipeline('summarization')

# Structured company information
company_info = {
    "services": ["Consulting", "Web Development", "SEO", "Using AI Marketing", "Lead Geneartion", "AI Chatbot"],
    "products": ["Product A", "Product B", "Product C"],
    "contact": {
        "phone": "7310441335",
        "email": "vshukla91827@gmail.com",
        "owner": "Saurabh Shukla"
    }
}

# Dictionary to store PDF summaries
pdf_summaries = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_email(subject, recipient, body):
    msg = Message(subject, sender='your-email@example.com', recipients=[recipient])
    msg.body = body
    mail.send(msg)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_answer', methods=['POST'])
def get_answer():
    data = request.json
    question = data.get('question', '').strip().lower()
    
    if 'services' in question:
        response = "We offer the following services: " + ", ".join(company_info['services'])
    elif 'products' in question:
        response = "We have the following products: " + ", ".join(company_info['products'])
    elif 'contact' in question or 'phone' in question or 'email' in question or 'owner' in question:
        contact_info = company_info['contact']
        response = ("Contact with us using "
            f"Phone No: {contact_info['phone']}\n"
            f"Email: {contact_info['email']}\n"
            f"Owner: {contact_info['owner']}"
        )
    elif 'schedule a meeting' in question:
        response = "Please provide the following details to schedule a meeting:\n\n1. Your name\n2. Your email\n3. Your phone number\n4. Preferred date and time (YYYY-MM-DDTHH:MM)"
    elif 'upload pdf' in question or 'pdf' in question:
        response = "You can upload a PDF using the 'Upload PDF' button on the website. After uploading, the content will be processed and summarized."
    else:
        response = "I'm not sure how to respond to that. Can you please specify your request?"

    return jsonify({'answer': response})

@app.route('/schedule_meeting', methods=['POST'])
def schedule_meeting():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    datetime_str = data.get('datetime')

    try:
        appointment_time = datetime.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
        appointment_details = f"Name: {name}\nEmail: {email}\nPhone: {phone}\nScheduled Time: {appointment_time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Send email
        send_email("Meeting Scheduled", 'vshukla91827@gmail.com', appointment_details)

        return jsonify({'message': 'Your meeting has been scheduled. A confirmation email has been sent.'})
    except ValueError:
        return jsonify({'message': 'Invalid date format. Please use the correct format.'})

@app.route('/save_company_info', methods=['POST'])
def save_company_info():
    global company_info
    data = request.json
    company_info = data.get('info')
    return jsonify({'message': 'Company information has been saved.'})

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({'message': 'No file part.'})
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'message': 'No selected file.'})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extract text from PDF
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfFileReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        
        # Summarize text
        summary = summarizer(text, max_length=150, min_length=30, do_sample=False)[0]['summary_text']
        
        # Store the summary with the filename as key
        pdf_summaries[filename] = summary

        return jsonify({'message': 'PDF uploaded and processed.', 'summary': summary})
    else:
        return jsonify({'message': 'Invalid file type. Only PDF files are allowed.'})
    

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
