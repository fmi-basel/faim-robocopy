import smtplib
from email.mime.text import MIMEText


# TODO: Is this even used here?
# TODO: replace with faim-utils.
def send_mail(mailAdresse, mailObject, mailText):
    '''Sends a mail to the user about calculated times.

    '''
    try:
        msg = MIMEText(mailText)
        msg['Subject'] = mailObject
        msg['From'] = "Robocopy@fmi.ch"
        msg['To'] = mailAdresse

        s = smtplib.SMTP('cas.fmi.ch')  # TODO Move to separate config.
        s.sendmail("laurent.gelman@fmi.ch", mailAdresse,
                   msg.as_string())  # TODO This cant be right?
        s.quit()
    except:
        print("Could not send e-mail")
