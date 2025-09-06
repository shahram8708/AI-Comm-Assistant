"""Email utilities for connecting to IMAP and processing messages."""

import email
import imaplib
import os
import re
import uuid
from email.message import Message
from typing import List, Tuple

from flask import current_app

from ..config import Config
from ..extensions import db
from ..models import Thread, Email, Attachment
from ..utils import extract_keywords, calculate_priority


def _connect_imap() -> imaplib.IMAP4_SSL:
    """Connect to the IMAP server using either basic credentials or OAuth.

    Currently only basic username/password login is supported.  OAuth can be
    implemented by constructing an appropriate XOAUTH2 string.
    """
    host = Config.MAIL_IMAP_HOST
    port = Config.MAIL_IMAP_PORT
    user = Config.MAIL_IMAP_USER
    password = Config.MAIL_IMAP_PASSWORD
    imap = imaplib.IMAP4_SSL(host, port)
    imap.login(user, password)
    return imap


def fetch_and_store_emails(user_id: int) -> int:
    """Fetch new emails for the given user and persist them to the database.

    Returns the number of new emails processed.  The function filters messages
    based on subject keywords (support, query, request, help) and groups them
    into threads by thread ID or subject.  Attachments are saved to the
    attachments directory.
    """
    keywords = {'support', 'query', 'request', 'help'}
    count = 0
    try:
        imap = _connect_imap()
        imap.select(Config.MAIL_MAILBOX)
        # Search unseen messages; fallback to all
        status, data = imap.search(None, 'UNSEEN')
        mail_ids = data[0].split() if status == 'OK' else []
        for msg_id in mail_ids:
            status, msg_data = imap.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                continue
            msg_bytes = msg_data[0][1]
            message = email.message_from_bytes(msg_bytes)
            subject = message.get('Subject', '')
            if not any(k.lower() in subject.lower() for k in keywords):
                continue
            thread_identifier = message.get('Thread-Index') or message.get('Message-ID') or subject
            # Find or create Thread
            thread = Thread.query.filter_by(user_id=user_id, thread_id=thread_identifier).first()
            if not thread:
                thread = Thread(user_id=user_id, thread_id=thread_identifier, subject=subject)
                db.session.add(thread)
            # Parse email fields
            sender = email.utils.parseaddr(message.get('From'))[1]
            recipients = ','.join([email.utils.parseaddr(addr)[1] for addr in message.get_all('To', [])])
            body = _get_body_from_message(message)
            # Extract simple keywords and compute priority later
            extracted_keywords = extract_keywords(body)
            # Store Email
            email_record = Email(
                thread=thread,
                message_id=message.get('Message-ID'),
                sender=sender,
                recipients=recipients,
                subject=subject,
                body=body,
                keywords=','.join(extracted_keywords),
            )
            db.session.add(email_record)
            # Save attachments
            for part in message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if not filename:
                        continue
                    safe_name = f"{uuid.uuid4().hex}_{filename}"
                    # Store attachments outside of the package in a shared directory
                    attachments_dir = os.path.join(os.getcwd(), 'attachments')
                    os.makedirs(attachments_dir, exist_ok=True)
                    file_path = os.path.join(attachments_dir, safe_name)
                    with open(file_path, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    attachment = Attachment(email=email_record, filename=filename,
                                            content_type=part.get_content_type(), path=file_path)
                    db.session.add(attachment)
            # Update thread priority and metadata
            thread.priority_score = calculate_priority('neutral', False, email_record.timestamp)
            db.session.commit()
            count += 1
        imap.close()
        imap.logout()
    except Exception as e:
        current_app.logger.error(f"IMAP error: {e}")
    return count


def _get_body_from_message(message: Message) -> str:
    """Extract the plain text body from an email message."""
    body = ''
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == 'text/plain' and not part.get_filename():
                charset = part.get_content_charset() or 'utf-8'
                try:
                    body += part.get_payload(decode=True).decode(charset, errors='ignore')
                except Exception:
                    continue
    else:
        charset = message.get_content_charset() or 'utf-8'
        body = message.get_payload(decode=True).decode(charset, errors='ignore')
    return body