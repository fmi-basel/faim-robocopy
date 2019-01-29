import logging
import smtplib
from email.mime.text import MIMEText

from faim_common_utils.EmailConfig import smtpHost as DEFAULT_SMTPHOST

DEFAULT_SENDER = 'Robocopy@fmi.ch'


def send_mail(mail_address, mail_object, mail_text):
    '''Sends a mail to the user.

    '''
    try:
        msg = MIMEText(mail_text)
        msg['Subject'] = mail_object
        msg['From'] = DEFAULT_SENDER
        msg['To'] = mail_address

        with smtplib.SMTP(DEFAULT_SMTPHOST) as smtp_handle:
            smtp_handle.sendmail(DEFAULT_SENDER, mail_address, msg.as_string())

    except Exception as err:
        logging.getLogger(__name__).error('Could not send e-mail. Error: %s',
                                          str(err))
