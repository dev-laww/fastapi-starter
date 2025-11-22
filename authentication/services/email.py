from pathlib import Path
from typing import Dict, Union, List

import resend
from jinja2 import Environment, FileSystemLoader

from ..core.base import AppObject
from ..core.config import settings


class EmailService(AppObject):
    def __init__(self):
        resend.api_key = settings.resend_api_key
        template_path = Path(__file__).parent.parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_path)), autoescape=True
        )

    def __del__(self):
        resend.api_key = None

    def render_template(self, template_name: str, context: Dict):
        template = self.env.get_template(template_name)
        return template.render(context)

    def send_email(
        self, to_email: Union[str, List[str]], subject: str, html_content: str
    ):
        params = self.get_params(to_email, subject, html_content)
        email = resend.Emails.send(params)
        return email

    @staticmethod
    def get_params(
        to_email: Union[str, List[str]], subject: str, html_content: str
    ) -> resend.Emails.SendParams:
        return {
            "from": settings.resend_email_from,
            "to": to_email,
            "subject": subject,
            "html": html_content,
        }
