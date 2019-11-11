import re

PDF_URL = {
    "document": "https://docs.google.com/document/d/{file_id}/export?format=pdf",
    "presentation": "https://docs.google.com/presentation/d/{file_id}/export/pdf",
    "spreadsheets": "https://docs.google.com/spreadsheets/d/{file_id}/export?format=pdf",
}

ID_REGEX = r"([a-zA-Z]+)\/d\/([a-zA-Z0-9-_]+)"


def gpdf(doc, link, **kwargs):
    """generate pdf download link from google drive link to document or presentation

    :param doc: current document
    :type doc: Doc
    :param link: full url of document or presentation
    :type link: str
    :return: a download link to document/presentation as pdf
    :rtype: str
    """
    j = doc.docsite._j

    link = link.strip()
    match = re.search(ID_REGEX, link)
    if match:
        doc_type, file_id = match.groups()
        if doc_type not in PDF_URL:
            raise j.exceptions.Value(f"{doc_type} is not a supported document type")

        pdf_link = PDF_URL[doc_type].format(file_id=file_id)
        return f"[download as pdf]({pdf_link})"
    raise j.exceptions.Value(f"cannot extract document type of id from an invalid link '{link}''")
