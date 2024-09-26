import smtplib
import uuid
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import render_template, url_for
from itsdangerous import URLSafeTimedSerializer

from app.api import ALLOC_APPROVE_CONFIRM_TYPES, RC_SMALL_LOGO_URL

TEST_MESSAGES = []


class EmailService():

    def __init__(self, app):
        self.app = app

    def tracking_code(self):
        return str(uuid.uuid4())[:16]

    def email_server(self):
        server = smtplib.SMTP(host=self.app.config['MAIL_SERVER'],
                              port='25',
                              timeout=self.app.config['MAIL_TIMEOUT'])
        server.ehlo()
        if self.app.config['MAIL_USE_TLS']:
            server.starttls()
        if self.app.config['MAIL_USERNAME']:
            server.login(self.app.config['MAIL_USERNAME'],
                         self.app.config['MAIL_PASSWORD'])
        return server

    def send_email(self, subject, recipients, text_body, html_body, sender=None, ical=None, cc_recipinents=None):
        msgRoot = MIMEMultipart('related')
        msgRoot.set_charset('utf8')

        if (sender is None):
            sender = self.app.config['MAIL_DEFAULT_SENDER']

        msgRoot['Subject'] = Header(subject.encode('utf-8'), 'utf-8').encode()
        msgRoot['From'] = sender
        msgRoot['To'] = ', '.join(recipients)
        if (cc_recipinents is not None):
            recipients = recipients + cc_recipinents
            msgRoot['Cc'] = ', '.join(cc_recipinents)
        msgRoot.preamble = 'This is a multi-part message in MIME format.'

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)

        part1 = MIMEText(text_body, 'plain', _charset='UTF-8')
        part2 = MIMEText(html_body, 'html', _charset='UTF-8')

        msgAlternative.attach(part1)
        msgAlternative.attach(part2)

        if ical:
            ical_atch = MIMEText(ical.decode("utf-8"), 'calendar')
            ical_atch.add_header('Filename', 'event.ics')
            ical_atch.add_header('Content-Disposition',
                                 'attachment; filename=event.ics')
            msgRoot.attach(ical_atch)

        if 'TESTING' in self.app.config and self.app.config['TESTING']:
            print("TEST:  Recording Emails, not sending - %s - to:%s" %
                  (subject, recipients))
            TEST_MESSAGES.append(msgRoot)
            return

        server = self.email_server()
        server.sendmail(sender, recipients, msgRoot.as_string())
        server.quit()

    def send_hpc_allocation_confirm_email(self,
                                          from_email_address,
                                          to_email_address,
                                          subject, ticket_id,
                                          callback_host, content_dict):
        tracking_code = self.tracking_code()
        if (callback_host.endswith('/')):
            callback_host = callback_host[:-1]
        confirm_approve_url = ''.join(
            [
                callback_host,
                url_for(
                    "confirm_hpc_allocation_request", version="v2",
                    token=URLSafeTimedSerializer(self.app.config['MAIL_SECRET_KEY']).dumps(
                        ticket_id, salt=ALLOC_APPROVE_CONFIRM_TYPES[0]))
            ]
        )
        print("TEST APPROVAL URL: "+confirm_approve_url)
        confirm_disapprove_url = ''.join(
            [
                callback_host,
                url_for(
                    "confirm_hpc_allocation_request", version="v2",
                    token=URLSafeTimedSerializer(self.app.config['MAIL_SECRET_KEY']).dumps(
                        ticket_id, salt=ALLOC_APPROVE_CONFIRM_TYPES[1]))
            ]
        )
        confirm_part_approve_url = ''.join(
            [
                callback_host,
                url_for(
                    "confirm_hpc_allocation_request", version="v2",
                    token=URLSafeTimedSerializer(self.app.config['MAIL_SECRET_KEY']).dumps(
                        ticket_id, salt=ALLOC_APPROVE_CONFIRM_TYPES[2]))
            ]
        )

        current_date = datetime.now().strftime(
            "%A, %B %d, %Y - %H:%M")

        html_body = render_template(
            "confirm_email.html",
            logo_url=RC_SMALL_LOGO_URL,
            current_date=current_date,
            confirm_approve_url=confirm_approve_url.replace('httpss:','https'),
            confirm_disapprove_url=confirm_disapprove_url.replace('httpss:','https'),
            confirm_part_approve_url=confirm_part_approve_url.replace('httpss:','https'),
            tracking_code=tracking_code,
            content_dict=content_dict
        )

        text_body = render_template(
            "confirm_email.txt",
            current_date=current_date,
            confirm_approve_url=confirm_approve_url.replace('httpss:','https'),
            confirm_disapprove_url=confirm_disapprove_url.replace('httpss:','https'),
            confirm_part_approve_url=confirm_part_approve_url.replace('httpss:','https'),
            tracking_code=tracking_code,
            content_dict=content_dict

        )

        self.send_email(subject, sender=from_email_address,
                        recipients=to_email_address.split(','),
                        text_body=text_body,
                        html_body=html_body)

        return tracking_code

    def send_purchase_ack_email(self,
                                from_email_address,
                                to_email_address,
                                cc_email_addresses,
                                subject, ticket_id,
                                content_dict):
        tracking_code = self.tracking_code()

        current_date = datetime.now().strftime(
            "%A, %B %d, %Y - %H:%M")

        html_body = render_template(
            "purchase_ack.html",
            logo_url=RC_SMALL_LOGO_URL,
            current_date=current_date,
            ticket_id=ticket_id,
            tracking_code=tracking_code,
            content_dict=content_dict
        )

        text_body = render_template(
            "purchase_ack.txt",
            current_date=current_date,
            ticket_id=ticket_id,
            tracking_code=tracking_code,
            content_dict=content_dict
        )

        self.send_email(subject, sender=from_email_address,
                        recipients=[to_email_address],
                        cc_recipinents=cc_email_addresses,
                        text_body=text_body,
                        html_body=html_body)

        return tracking_code

    def send_storage_request_confirm_email(self,
                                          from_email_address,
                                          to_email_address,
                                          subject, ticket_id,
                                          callback_host, content_dict):
        tracking_code = self.tracking_code()
        if(callback_host.endswith('/')):
            callback_host = callback_host[:-1]
        confirm_approve_url = ''.join(
            [
                callback_host,
                url_for(
                    "confirm_storage_request", version="v2",
                    token=URLSafeTimedSerializer(self.app.config['MAIL_SECRET_KEY']).dumps(
                        ticket_id, salt=ALLOC_APPROVE_CONFIRM_TYPES[0]))
            ]
        )
        confirm_disapprove_url = ''.join(
            [
                callback_host,
                url_for(
                    "confirm_storage_request", version="v2",
                    token=URLSafeTimedSerializer(self.app.config['MAIL_SECRET_KEY']).dumps(
                        ticket_id, salt=ALLOC_APPROVE_CONFIRM_TYPES[1]))
            ]
        )
        confirm_part_approve_url = ''.join(
            [
                callback_host,
                url_for(
                    "confirm_storage_request", version="v2",
                    token=URLSafeTimedSerializer(self.app.config['MAIL_SECRET_KEY']).dumps(
                        ticket_id, salt=ALLOC_APPROVE_CONFIRM_TYPES[2]))
            ]
        )

        current_date = datetime.now().strftime(
            "%A, %B %d, %Y - %H:%M")

        html_body = render_template(
            "confirm_email_storage.html",
            logo_url=RC_SMALL_LOGO_URL,
            current_date=current_date,
            confirm_approve_url=confirm_approve_url.replace('httpss:','https'),
            confirm_disapprove_url=confirm_disapprove_url.replace('httpss:','https'),
            confirm_part_approve_url=confirm_part_approve_url.replace('httpss:','https'),
            tracking_code=tracking_code,
            content_dict=content_dict
        )

        text_body = render_template(
            "confirm_email_storage.txt",
            current_date=current_date,
            confirm_approve_url=confirm_approve_url.replace('httpss:','https'),
            confirm_disapprove_url=confirm_disapprove_url.replace('httpss:','https'),
            confirm_part_approve_url=confirm_part_approve_url.replace('httpss:','https'),
            tracking_code=tracking_code,
            content_dict=content_dict

        )
        print(text_body)
        self.send_email(subject, sender=from_email_address,
                        recipients=to_email_address.split(','),
                        text_body=text_body,
                        html_body=html_body)

        return tracking_code

    def send_storage_purchase_ack_email(self,
                                from_email_address,
                                to_email_address,
                                cc_email_addresses,
                                subject, ticket_id,
                                content_dict):
        tracking_code = self.tracking_code()

        current_date = datetime.now().strftime(
            "%A, %B %d, %Y - %H:%M")

        html_body = render_template(
            "purchase_ack_storage.html",
            logo_url=RC_SMALL_LOGO_URL,
            current_date=current_date,
            ticket_id=ticket_id,
            tracking_code=tracking_code,
            content_dict=content_dict
        )

        text_body = render_template(
            "purchase_ack_storage.txt",
            current_date=current_date,
            ticket_id=ticket_id,
            tracking_code=tracking_code,
            content_dict=content_dict
        )

        self.send_email(subject, sender=from_email_address,
                        recipients=[to_email_address],
                        cc_recipinents=cc_email_addresses,
                        text_body=text_body,
                        html_body=html_body)

        return tracking_code