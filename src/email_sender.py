from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send_email(subject: str, html_body: str) -> None:
    host = _required_env("EMAIL_HOST")
    port = int(_required_env("EMAIL_PORT"))
    username = _required_env("EMAIL_USER")
    password = _required_env("EMAIL_PASSWORD")
    sender = _required_env("EMAIL_FROM")
    recipients = _parse_recipients(_required_env("EMAIL_TO"))

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content("请使用支持 HTML 的邮件客户端查看本简报。")
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message, to_addrs=recipients)


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _parse_recipients(value: str) -> list[str]:
    recipients = [email.strip() for email in value.split(",") if email.strip()]
    if not recipients:
        raise RuntimeError("EMAIL_TO must include at least one recipient.")
    return recipients
