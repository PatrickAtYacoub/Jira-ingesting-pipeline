
import os
from typing import List
from abc import ABC, abstractmethod#
import json
from lib.project_path import ProjectPath
from model.jira_models import JiraAttachement, JiraBaseIssue
from ai.prompting import prompt_with_image
from ai.prompt_store import PromptStore
from file_processing.pdf_analyzing import PDFIngestApplication
from file_processing.document_types import get_file_object, AbstractDocument, AbstractImageDocument
from lib.logger import logger

class AttachmentExtractor(ABC):
    """
    Interface for attachment extractors.
    Defines methods for extracting content from different types of attachments.
    """

    def __init__(self, doc:AbstractDocument):
        """
        Initialize the extractor with the file path.
        Args:
            file_path (str): The path to the file to be processed.
        """
        self.doc = doc

    @abstractmethod
    def extract(self, base_path=None) -> str:
        """
        Extract content from the given file.
        Args;
            base_path (str): The base path for the file.
        Returns:
            str: The extracted content.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def get_meta_data(self) -> dict:
        """
        Get metadata from the given file.
        Returns:
            dict: The extracted metadata.
        """
        # Implement metadata extraction logic here
        raise NotImplementedError("Subclasses must implement this method")


class AttachementHandler:
    """
    A class to handle Jira attachments.
    This class provides methods to retrieve the content of attachments
    and to process them as needed.
    """
    def __init__(self, jira_client):
        self.jira_client = jira_client
        self.base_path = ProjectPath.local('[]/tmp/fileblobs')  # Ensure a valid path is provided

        absolute_path = ProjectPath.absolute(self.base_path)
        if not os.path.exists(absolute_path):
            os.makedirs(absolute_path)

    def get_attachment_content(self, attachement:JiraAttachement):
        """
        Get the content of a Jira attachment.
        Args:
            attacgenent (JiraAttachement): The Jira attachment object.
        Returns:
            bytes: The content of the attachment.
        """
        return attachement.get_content(self.jira_client)

    def save_attachment_local(self, attachement:JiraAttachement, filename=None):
        """
        Save the attachment content to a file.
        Args:
            attachement (JiraAttachement): The Jira attachment object.
        Returns:
            str: The path to the saved file.
        """
        content = self.get_attachment_content(attachement)
        new_filename = filename if filename else attachement.filename
        filename = f"{self.base_path}/{new_filename}"

        with open(filename, "wb") as f:
            f.write(content)

        return filename

    def describe_attachement(self, attachement:JiraAttachement, prompt:str=None):
        """
        Describe the attachment using a prompt.
        Args:
            attachement (JiraAttachement): The Jira attachment object.
            prompt (str): The prompt to describe the attachment.
            If None, a default prompt will be used.
        Returns:
            str: The description of the attachment.
        """
        content = self.get_attachment_content(attachement)
        prompt = prompt or "Beschreibe das Bild in einem KI-Model optimierten Format."
        response = prompt_with_image(content, prompt)
        return response

    def process_attachements(self, jira_issue: List[JiraBaseIssue], save_file=False) -> List[str]:
        """
        Process all attachments in a Jira issue and return their descriptions.
        Args:
            jira_issue (JiraBaseIssue): The Jira issue object containing attachments.
            If None, a default prompt will be used.
        Returns:
            List[str]: A list of descriptions for each attachment.
        """
        res_object = {}
        for attachement in jira_issue.attachments:
            fn = attachement.filename
            # description = self.describe_attachement(attachement, prompt)
            # descriptions.append(description)
            if save_file:
                _filename = f"{jira_issue.key}_{attachement.filename}"
                filename = self.save_attachment_local(attachement, filename=_filename)
                logger.info(f"Attachment saved to {filename}")

            document = get_file_object(fn if not save_file else filename)
            extension = document.get_file_extension()
            if extension not in handlers:
                logger.warning(f"No handler found for file type: {extension}. Skipping attachment.")
                continue
            hdlr = handlers.get(extension, None)(document)
            res_object[attachement.filename] = {
                'meta_data': hdlr.get_meta_data(),
                'content': hdlr.extract(base_path=self.base_path),
            }

        return res_object


# handlers

class PDFExtractor(AttachmentExtractor):
    """
    Extractor for PDF files.
    """

    def extract(self, base_path=None) -> str:
        fn = f"{base_path if base_path else ''}/{self.doc.filename}"
        content = PDFIngestApplication.run(fn)
        elements = []
        for chunk in content:
            cnt = content[chunk]
            elements.append(f"{cnt.chapter}{'\n' if cnt.chapter else ''}{cnt.section}\n{' '.join(cnt.texts)}")
        return elements

    def get_meta_data(self) -> dict:
        # Implement PDF metadata extraction logic here
        return self.doc.get_path_attributes().model_dump_json()


class ImageExtractor(AttachmentExtractor):
    """
    Extractor for image files.
    """
    def extract(self, base_path=None) -> str:
        fn = f"{base_path + '/' if base_path else ''}{self.doc.filename}"
        with open(fn, "rb") as f:
            content = f.read()
        prompt = PromptStore.get_prompt('describe', object='image', recipient='ai_model', format='contextual_search')
        res = prompt_with_image(content, prompt)
        return res

    def get_meta_data(self) -> dict:
        # Implement image metadata extraction logic here
        self.doc.get_path_attributes().model_dump_json()

handlers = {
    "pdf": PDFExtractor,
    "jpg": ImageExtractor,
    "jpeg": ImageExtractor,
    "png": ImageExtractor,
    # Add more handlers as needed
}