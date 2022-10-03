import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yaml
from yaml.loader import SafeLoader

with open("mail_info.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)


def send_mail(message):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = cfg["sender_mail"]  # Enter your address
    receiver_email = cfg["receiver_mail"]  # Enter receiver address
    password = cfg["sender_password"]
    final_message = MIMEMultipart("alternative")
    final_message["Subject"] = "Kraken Trader Encountered an Error"
    final_message["From"] = cfg["sender_mail"]
    final_message["To"] = cfg["receiver_mail"]
    text = f"""\
    The message was:
    {message}"""
    part1 = MIMEText(text, "plain")
    final_message.attach(part1)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, final_message.as_string())
