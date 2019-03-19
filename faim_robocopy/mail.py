import logging
import smtplib
from email.mime.text import MIMEText


def send_mail(receiver_address, mail_subject, mail_text, smtphost,
              sender_address):
    '''Sends a mail to the user.

    '''
    try:
        msg = MIMEText(mail_text)
        msg['Subject'] = mail_subject
        msg['From'] = sender_address
        msg['To'] = receiver_address

        with smtplib.SMTP(smtphost) as smtp_handle:
            smtp_handle.sendmail(sender_address, receiver_address,
                                 msg.as_string())

    except Exception as err:
        logging.getLogger(__name__).error('Could not send e-mail. Error: %s',
                                          str(err))
