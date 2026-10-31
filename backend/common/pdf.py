from io import BytesIO

from django.template.loader import render_to_string


def render_pdf(template, context):
    """Render a template to PDF bytes. WeasyPrint needs Pango, which Windows
    machines often lack, so xhtml2pdf is the fallback."""
    html = render_to_string(template, context)
    try:
        from weasyprint import HTML

        return HTML(string=html).write_pdf()
    except OSError:
        from xhtml2pdf import pisa

        out = BytesIO()
        result = pisa.CreatePDF(html, dest=out)
        if result.err:
            raise RuntimeError("PDF generation failed")
        return out.getvalue()
