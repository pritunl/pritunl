from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings

import smtplib
import email.mime.multipart
import email.mime.text

def send_email(to_addr, subject, text_body, html_body):
    from pritunl import logger

    email_server = settings.app.email_server
    email_from_addr = settings.app.email_from_addr
    email_username = settings.app.email_username
    email_password = settings.app.email_password

    if not email_server or not email_from_addr or not \
            email_username or not email_password:
        raise EmailNotConfiguredError('Email not configured')

    msg = email.mime.multipart.MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = email_from_addr
    msg['To'] = to_addr

    msg.attach(email.mime.text.MIMEText(text_body, 'plain'))
    msg.attach(email.mime.text.MIMEText(html_body, 'html'))

    try:
        smtp_conn = smtplib.SMTP_SSL(email_server)
        smtp_conn.login(email_username, email_password)
        smtp_conn.sendmail(email_from_addr, to_addr, msg.as_string())
        smtp_conn.quit()
    except smtplib.SMTPAuthenticationError:
        raise EmailAuthInvalid('Email auth is invalid')
    except smtplib.SMTPSenderRefused:
        raise EmailAuthInvalid('Email from address refused')
    except:
        logger.exception('Unknown smtp error', 'utils',
            from_addr=email_from_addr,
            to_addr=to_addr,
        )
        raise
