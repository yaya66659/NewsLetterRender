from flask import Flask, render_template, request
import smtplib, csv, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import chardet


load_dotenv()  # facultatif sur Render, utile en local

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EMAIL_SENDER = os.getenv("GMAIL_SENDER")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
ADMIN_PASSWORD = os.getenv("APP_ADMIN_PASSWORD")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form.get("motdepasse") != ADMIN_PASSWORD:
            return "⛔ Mot de passe incorrect."

        sujet = request.form['sujet']
        corps_html = request.form['corps']
        fichier = request.files['fichier_csv']
        chemin = os.path.join(UPLOAD_FOLDER, fichier.filename)
        fichier.save(chemin)

        try:
            
          with open(chemin, 'rb') as   f:
           raw_data = f.read()
           encodage_detecte =.                         chardet.detect(raw_data)['encoding']

           with open(chemin,  newline='', encoding=encodage_detecte)  as f:
            reader = csv.DictReader(f)
            for row in reader:
            prenom = row.get("Prenom", "")
            email = row.get("Email", "")
           corps_personnalise = corps_html.replace("{prenom}", prenom)
           envoyer_email(email, sujet, corps_personnalise)
        finally:
            os.remove(chemin)

        return "✅ Emails envoyés avec succès !"

    return render_template("index.html")

@app.route('/preview', methods=['POST'])
def preview():
    corps_html = request.form['corps']
    return f"<div style='padding:2rem'>{corps_html}</div>"

def envoyer_email(destinataire, sujet, contenu_html):
    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_SENDER
    msg["To"] = destinataire
    msg["Subject"] = sujet
    msg.attach(MIMEText(contenu_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as serveur:
        serveur.login(EMAIL_SENDER, APP_PASSWORD)
        serveur.send_message(msg)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
