"""Module to parse technical documentation file paths and extract metadata."""

from datetime import datetime
import os
from typing import Dict
from pydantic import BaseModel, Field
from pypdf import PdfReader
from PIL import Image
from PIL.ExifTags import TAGS


class TechnicalDocumentationFilePathParser:
    """Parses the file path of a technical document."""

    def __init__(self, filepath: str) -> None:
        """
        Initializes the parser with a file path.

        Args:
            filepath (str): The full path to the file.
        """
        self.filepath = filepath

    def preprocess(self) -> str:
        """
        Extracts the filename from the full file path.

        Returns:
            str: The extracted filename.
        """
        return self.filepath.split('/')[-1]

    def get_filename(self) -> str:
        """
        Returns the filename.

        Returns:
            str: The filename.
        """
        return self.filepath.split('/')[-1]

    def get_file_extension(self) -> str:
        """
        Returns the file extension.

        Returns:
            str: The file extension.
        """
        return self.filepath.split('.')[-1]


class BaseFileModel(BaseModel):
    """Base model containing the filename."""

    filename: str = Field(..., description="The name of the file")
    created: str | None = Field(
        None, description="The creation date of the file in 'YYYY-MM-DD HH:MM:SS' format"
    )
    modified: str | None = Field(
        None, description="The modification date of the file in 'YYYY-MM-DD HH:MM:SS' format"
    )

class ImageFileModel(BaseFileModel):
    """Model containing metadata for an image file."""

    width: int | None = Field(None, description="Width of the image in pixels")
    height: int | None = Field(None, description="Height of the image in pixels")
    format: str | None = Field(None, description="Format of the image (e.g., JPEG, PNG)")


class TechnicalDocumentationFileData(BaseFileModel):
    """Model containing metadata for a technical documentation file."""

    article_number: str
    document_type: str
    language: str
    version: str


class AbstractDocument:
    """Abstract document base class for handling file metadata."""

    def __init__(self, filepath: str) -> None:
        """
        Initializes the document by parsing the file path.

        Args:
            filepath (str): The full path to the document file.
        """
        parser = TechnicalDocumentationFilePathParser(filepath)
        self.filename: str = parser.preprocess()
        self.created: str | None = None
        self.modified: str | None = None
        self.path_attributes: BaseFileModel  # To be defined in subclass

    def get_file_extension(self) -> str:
        """
        Returns the file extension of the document.

        Returns:
            str: The file extension.
        """
        return self.filename.split('.')[-1]

    def get_path_attributes(self) -> BaseFileModel:
        """
        Returns the parsed path attributes.

        Returns:
            BaseFileModel: The model containing parsed file metadata.
        """
        return self.path_attributes

    def set_created(self, created: str) -> None:
        """
        Sets the creation date of the document.

        Args:
            created (str): The creation date in string format.
        """
        try:
            datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError(
                "The 'created' attribute must be in the format 'YYYY-MM-DD HH:MM:SS'."
                ) from exc
        self.created = created
        self.path_attributes.created = created

    def set_modified(self, modified: str) -> None:
        """
        Sets the modification date of the document.

        Args:
            modified (str): The modification date in string format.
        """
        try:
            datetime.strptime(modified, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError(
                "The 'modified' attribute must be in the format 'YYYY-MM-DD HH:MM:SS'."
            ) from exc
        self.modified = modified
        self.path_attributes.modified = modified


class AbstractPDFDocument(AbstractDocument):
    """Abstract class for handling PDF documents."""

    def __init__(self, filepath: str) -> None:
        """
        Initializes the PDF document by parsing the file path.

        Args:
            filepath (str): The full path to the PDF document file.
        """
        super().__init__(filepath=filepath)
        self.path_attributes = BaseFileModel(filename=self.filename)
        if not os.path.exists(filepath):
            return
        self.reader = PdfReader(filepath)

        self._set_dates_from_pdf_metadata()

    @staticmethod
    def is_pdf(filepath: str) -> bool:
        """
        Checks if the file is a PDF.

        Args:
            filepath (str): The full path to the file.

        Returns:
            bool: True if the file is a PDF, False otherwise.
        """
        return filepath.lower().endswith('.pdf')

    def _set_dates_from_pdf_metadata(self) -> None:
        """
        Extracts and sets the creation and modification dates from the PDF metadata.
        """
        metadata = self.reader.metadata
        if metadata:
            created = metadata.get('/CreationDate')
            if created:
                parsed = self._parse_pdf_date(created)
                if parsed:
                    self.set_created(parsed)

            modified = metadata.get('/ModDate')
            if modified:
                parsed = self._parse_pdf_date(modified)
                if parsed:
                    self.set_modified(parsed)

    def _parse_pdf_date(self, date_str: str) -> str | None:
        """
        Parses a PDF date string in the format 'D:YYYYMMDDHHmmSS' to 'YYYY-MM-DD HH:MM:SS'.

        Args:
            date_str (str): The raw PDF date string.

        Returns:
            str | None: The formatted date string or None if parsing fails.
        """
        try:
            if date_str.startswith("D:"):
                date_str = date_str[2:]
            # Use the full date and time part: YYYYMMDDHHmmSS
            return datetime.strptime(date_str[:14], "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


class TechnicalDocumentation(AbstractPDFDocument):
    """Represents a technical documentation file with structured metadata."""

    document_types: Dict[str, str] = {
        "hdb": "Handbuch",
        "ina": "Installationsanweisung",
    }

    def __init__(self, filepath: str) -> None:
        """
        Parses the filename and extracts structured metadata.

        Args:
            filepath (str): The full path to the technical documentation file.

        Raises:
            ValueError: If the file format does not contain all required parts.
        """
        super().__init__(filepath=filepath)

        file_parts = self.filename.split('_')
        if len(file_parts) < 4:
            raise ValueError(f"Invalid file format: {filepath}")

        file_type = self.document_types.get(file_parts[1].lower(), "Unknown")

        self.path_attributes = TechnicalDocumentationFileData(
            article_number=file_parts[0],
            document_type=file_type,
            language=file_parts[2],
            version=file_parts[3].replace('.pdf', ''),
            filename=self.filename
        )

    @staticmethod
    def is_technical_document(filepath: str) -> bool:
        """
        Checks if the file is a technical documentation file.

        Args:
            filepath (str): The full path to the file.

        Returns:
            bool: True if the file is a technical documentation file, False otherwise.
        """
        filename = os.path.basename(filepath)
        basic_requirements = len(filename.split('_')) >= 4 and filename.endswith('.pdf')
        correct_type = basic_requirements and filename.split('_')[1].lower() in TechnicalDocumentation.document_types
        return correct_type
    


class AbstractImageDocument(AbstractDocument):
    """Abstract class for handling image documents."""

    def __init__(self, filename: str):
        super().__init__(filename)
        self.created = None
        self.modified = None

        if os.path.exists(filename):
            try:
                with Image.open(filename) as image:
                    exif_data = image._getexif()  # pylint: disable=protected-access
                    if exif_data:
                        for tag, value in exif_data.items():
                            tag_name = TAGS.get(tag, tag)
                            if tag_name == "DateTimeOriginal":
                                try:
                                    self.created = datetime.strptime(
                                        value, "%Y:%m:%d %H:%M:%S"
                                    )
                                except (ValueError, TypeError):
                                    pass

                if self.created is None:
                    self.created = datetime.fromtimestamp(
                        os.path.getctime(filename)
                    )

                self.modified = datetime.fromtimestamp(
                    os.path.getmtime(filename)
                )

                self.width, self.height = image.size

            except (OSError, ValueError) as err:
                print(f"Fehler beim Lesen von {self.filename}: {err}")

        self.path_attributes = ImageFileModel(
            filename=self.filename,
            created=self.created.strftime("%Y-%m-%d %H:%M:%S") if self.created else None,
            modified=self.modified.strftime("%Y-%m-%d %H:%M:%S") if self.modified else None,
            format=self.get_file_extension(),
            width=self.width if hasattr(self, 'width') else None,
            height=self.height if hasattr(self, 'height') else None,
        )

    @staticmethod
    def is_image(filepath: str) -> bool:
        """
        Checks if the file is an image.

        Args:
            filepath (str): The full path to the file.

        Returns:
            bool: True if the file is an image, False otherwise.
        """
        return filepath.lower().endswith(('.jpg', '.jpeg', '.png'))
    

def get_file_object(filepath: str) -> AbstractDocument:
    """
    Returns an instance of the appropriate document class based on the file type.

    Args:
        filepath (str): The full path to the file.

    Returns:
        AbstractDocument: An instance of the appropriate document class.
    """
    if TechnicalDocumentation.is_technical_document(filepath):
        return TechnicalDocumentation(filepath)
    elif AbstractPDFDocument.is_pdf(filepath):
        return AbstractPDFDocument(filepath)
    elif AbstractImageDocument.is_image(filepath):
        return AbstractImageDocument(filepath)
    else:
        return AbstractDocument(filepath)


if __name__ == "__main__":
    # FILEPATH = "tmp/fileblobs/DATA-76_DATA-Cloud Connector for Replication Flows-291124-131723.pdf"
    # is_technical_doc = TechnicalDocumentation.is_technical_document(FILEPATH)
    # print(f"Is technical document: {is_technical_doc}")
    # doc = get_file_object(FILEPATH)
    # attributes = doc.get_path_attributes()
    # print(attributes.model_dump_json(indent=2))

    print(AbstractImageDocument('tmp/fileblobs/DATA-47_image-20241114-140519.png').get_path_attributes().model_dump_json())
