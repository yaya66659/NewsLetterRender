from flask import Flask, render_template, request
import smtplib, csv, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import chardet

load_dotenv()

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
            with open(chemin, 'rb') as f:
                raw_data = f.read()
                detection = chardet.detect(raw_data)
                encodage_detecte = detection['encoding'] or 'utf-8'
                if encodage_detecte.lower() in ['ascii', 'iso-8859-1'] and b'\x00' in raw_data:
                    encodage_detecte = 'utf-16'

            with open(chemin, newline='', encoding=encodage_detecte) as f:
                # Lecture brut pour détecter le séparateur
                debut = f.read(1000)
                f.seek(0)
                sep = '\t' if debut.count('\t') > debut.count(',') else ','
                
                reader = csv.DictReader(f, delimiter=sep)
                reader.fieldnames = [name.lstrip('\ufeff') for name in reader.fieldnames]

                mails_envoyes = 0
                for row in reader:
                    prenom = row.get("Prenom", "").strip()
                    email = row.get("Email", "").strip()
                    if not email:
                        print(f"❌ Email vide pour la ligne : {row}")
                        continue
                    corps_personnalise = corps_html.replace("{prenom}", prenom)
                    envoyer_email(email, sujet, corps_personnalise)
                    mails_envoyes += 1

                print(f"✅ {mails_envoyes} mails envoyés.")

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
