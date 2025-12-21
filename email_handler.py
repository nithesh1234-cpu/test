"""A common utility for sending mails."""

import smtplib
import logging

LOGGER = logging.getLogger(__name__)


def email_handler(to_user, cc_users, subject, message, user_name, password, host, port):
    """This is a common method to send emails.
        @param to_user: a string containing the to user.
        @param cc_users: an array containing the cc users
        @param subject: subject string
        @param message: MIMEMultipart class object
        @param user_name: user name to send email
        @param password: password to use with user name
        @param host: email client host
        @param port: port number for mail client
        @return: None
    """

    distribution_list = {'To': to_user,
                         'CC': cc_users}
    message['From'] = user_name
    message['To'] = distribution_list["To"]
    message['CC'] = ",".join(distribution_list["CC"])
    receivers = [message['To']] + list(distribution_list["CC"])
    message['Subject'] = subject

    text = message.as_string()

    try:
        smtp_obj = smtplib.SMTP_SSL(host, port)
        smtp_obj.login(user_name, password)
        smtp_obj.sendmail(user_name, receivers, text)
        LOGGER.info("Successfully sent email")
    except smtplib.SMTPException as error:
        LOGGER.error("Error: unable to send email : %s", error)
