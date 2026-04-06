# import logging
# from pathlib import Path
# from jinja2 import Environment, FileSystemLoader
# from weasyprint import HTML

# logger = logging.getLogger(__name__)

# TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


# class PDFGenerator:

#     def __init__(self):
#         self.env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

#     def generate_cv(self, cv_data: dict) -> bytes:
#         try:
#             template = self.env.get_template("cv.html")
#             html_content = template.render(cv=cv_data)
#             return HTML(string=html_content).write_pdf()
#         except Exception as e:
#             logger.error(f"CV PDF generation error: {e}")
#             raise

#     def generate_cover_letter(self, content: str, personal: dict = {}) -> bytes:
#         try:
#             template = self.env.get_template("cover_letter.html")
#             html_content = template.render(content=content, personal=personal)
#             return HTML(string=html_content).write_pdf()
#         except Exception as e:
#             logger.error(f"Cover letter PDF generation error: {e}")
#             raise

import logging
import io
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


class PDFGenerator:

    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    def _html_to_pdf(self, html: str) -> bytes:
        buffer = io.BytesIO()
        result = pisa.CreatePDF(io.StringIO(html), dest=buffer)
        if result.err:
            raise Exception(f"PDF generation failed with {result.err} errors")
        return buffer.getvalue()

    def generate_cv(self, cv_data: dict) -> bytes:
        try:
            template = self.env.get_template("cv.html")
            html_content = template.render(cv=cv_data)
            return self._html_to_pdf(html_content)
        except Exception as e:
            logger.error(f"CV PDF generation error: {e}")
            raise

    def generate_cover_letter(self, content: str, personal: dict = {}) -> bytes:
        try:
            template = self.env.get_template("cover_letter.html")
            html_content = template.render(content=content, personal=personal)
            return self._html_to_pdf(html_content)
        except Exception as e:
            logger.error(f"Cover letter PDF generation error: {e}")
            raise