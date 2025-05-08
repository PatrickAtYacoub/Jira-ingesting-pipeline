import json
import re
import base64
from collections import defaultdict
from typing import List, Dict, Any
from pydantic import BaseModel
from ai.prompting import prompt_with_image
from lib.yacoub_asset import send_request

PAGE_HEIGHT = 842  # Constant for page height


class BBox(BaseModel):
    """
    Represents a bounding box with coordinates and coordinate origin.

    Attributes:
        t (float): Top coordinate.
        l (float): Left coordinate.
        b (float): Bottom coordinate.
        r (float): Right coordinate.
        coord_origin (str): Origin of the coordinate system (default: 'BOTTOMLEFT').
    """

    t: float  # top
    l: float  # left
    b: float  # bottom
    r: float  # right
    coord_origin: str = "BOTTOMLEFT"

    @staticmethod
    def from_element_dictionary(element):
        """
        Creates a BBox object from a dictionary.

        Args:
            element (Dict[str, Any]): A dictionary containing bounding box data.

        Returns:
            BBox: The created bounding box object.
        """
        return BBox(
            t=element.get("t", float("inf")),
            l=element.get("l", float("inf")),
            b=element.get("b", PAGE_HEIGHT),
            r=element.get("r", 0),
            coord_original=element.get("coord_origin", "BOTTOMLEFT"),
        )


class Prov(BaseModel):
    """
    Metadata about an element, including its bounding box and page number.

    Attributes:
        bbox (BBox): The bounding box of the element.
        page_number (int): The page number where the element appears.
    """

    bbox: BBox
    page_number: int = 0

    @staticmethod
    def from_element_dictionary(element):
        """
        Creates a Prov object from a dictionary.

        Args:
            element (List[Dict[str, Any]]): A list containing dictionaries with element metadata.

        Returns:
            Prov: The created Prov object.
        """
        return Prov(
            bbox=BBox.from_element_dictionary(element[0].get("bbox", {})),
            page_number=element[0].get("page_no", 0),
        )


class SectionData(BaseModel):
    """
    Structured information about a section in the document.

    Attributes:
        chapter (str): Chapter label.
        section (str): Section heading.
        page_header (str): Page header text.
        texts (List[str]): List of associated text elements.
        prov (Prov): Metadata about the section's position in the document.
    """

    chapter: str
    section: str
    page_header: str
    texts: List[str]
    prov: Prov


# Utility Functions
class BoundingBoxUtils:
    """
    Utility class for processing bounding boxes, such as coordinate conversion and merging.
    """

    @staticmethod
    def recalculate_bbox_topleft2bottomleft(bbox: BBox) -> BBox:
        """
        Utility class for processing bounding boxes, such as coordinate conversion and merging.
        """
        updated_bbox = bbox.model_copy()
        updated_bbox.b = PAGE_HEIGHT - updated_bbox.b
        updated_bbox.t = PAGE_HEIGHT - updated_bbox.t
        updated_bbox.coord_original = "BOTTOMLEFT"
        return updated_bbox

    @staticmethod
    def update_bbox(current_bbox: BBox, new_bbox: BBox):
        """
        Updates an existing bounding box with new extremities.

        Args:
            current_bbox (BBox): The current bounding box to update.
            new_bbox (BBox): The new bounding box to merge with.
        """
        current_bbox.t = min(current_bbox.t, new_bbox.t)
        current_bbox.l = min(current_bbox.l, new_bbox.l)
        current_bbox.b = max(current_bbox.b, new_bbox.b)
        current_bbox.r = max(current_bbox.r, new_bbox.r)


# Factory Pattern for Decoding Images
class ImageDecoderFactory:
    """
    Factory class for decoding base64-encoded images.
    """

    @staticmethod
    def decode_base64_image(image_uri: str) -> bytes:
        """
        Decodes a base64-encoded image string.

        Args:
            image_uri (str): The URI or raw base64 string of the image.

        Returns:
            bytes: The decoded image content as bytes.
        """
        if "," in image_uri:
            image_uri = image_uri.split(",")[1]
        image_uri = image_uri.strip()
        image_uri += "=" * (-len(image_uri) % 4)  # Padding correction
        return base64.b64decode(image_uri)


# Section Processor
class SectionProcessor:
    """
    Responsible for splitting document content into structured sections.
    """

    @staticmethod
    def split_elements_by_section(elements: Dict[str, Any]) -> Dict[str, SectionData]:
        """
        Splits elements into sections based on labels and structure.

        Args:
            elements (Dict[str, Any]): The raw elements extracted from the document.

        Returns:
            Dict[str, SectionData]: A dictionary mapping section keys to SectionData objects.
        """
        sections = defaultdict(
            lambda: SectionData(
                chapter="",
                section="",
                page_header="",
                texts=[],
                prov=Prov(
                    bbox=BBox(t=float("inf"), l=float("inf"), b=PAGE_HEIGHT, r=0)
                ),
            )
        )

        current_key = None
        current_chapter = ""
        current_page_header = ""
        used_images = set()

        for element in elements.get("content", []):
            prov = Prov.from_element_dictionary(element.get("prov", {}))
            bbox = prov.bbox
            text = element.get("text", "")

            if element.get("label") == "section_header":
                match = re.match(r"^(\d+(?:\.\d+)*)(?:\s+)(.+)", text)
                if match:
                    hierarchy = match.group(1)
                    hierarchy_level = hierarchy.count(".")

                    current_key = SectionProcessor.build_key(prov)

                    current_chapter = SectionProcessor.set_chapter(
                        current_chapter, hierarchy_level, text
                    )
                    sections[current_key].chapter = current_chapter
                    continue

                current_key = SectionProcessor.build_key(prov)

                sections[current_key].chapter = current_chapter
                sections[current_key].section = text
                sections[current_key].page_header = current_page_header
                sections[current_key].prov.page_number = prov.page_number
                sections[current_key].prov.bbox.t = bbox.t
                sections[current_key].prov.bbox.l = bbox.l

            elif element.get("label") == "page_header":
                current_page_header = text

            elif element.get("label") == "table":
                table_elements = SectionProcessor.get_table_content(element)
                sections[current_key].texts.extend(table_elements)
                BoundingBoxUtils.update_bbox(sections[current_key].prov.bbox, bbox)

            elif (
                "pictures" in element.get("parent", {}).get("$ref", "")
                and element.get("parent").get("$ref") not in used_images
            ):
                used_images.add(element.get("parent").get("$ref"))
                matching_picture = next(
                    (
                        pic
                        for pic in elements.get("pictures", [])
                        if pic.get("self_ref") == element.get("parent").get("$ref")
                    ),
                    None,
                )
                if matching_picture:
                    image_uri = matching_picture.get("image", {}).get("uri", "")
                    decoded_image_uri = ImageDecoderFactory.decode_base64_image(
                        image_uri
                    )
                    image_description = prompt_with_image(
                        decoded_image_uri,
                        f"""Was ist auf dem Bild zur Überschrift {sections[current_key].chapter},
                        {sections[current_key].section} zu sehen?
                        Beschreibe fachlich und prägnant für ein anderes KI-Modell.""",
                    )
                    sections[current_key].texts.append(image_description)

            elif current_key:
                sections[current_key].texts.append(text)
                BoundingBoxUtils.update_bbox(sections[current_key].prov.bbox, bbox)

        # Bereinigen von Einträgen ohne Texte
        for key in list(sections.keys()):
            if not sections[key].texts:
                del sections[key]

        return sections

    @staticmethod
    def build_key(prov: Prov):
        """
        Builds a unique key based on bounding box and page number.

        Args:
            prov (Prov): Metadata for the element.

        Returns:
            str: A unique key representing the element's position.
        """
        return f"{int(prov.bbox.t)}_{int(prov.bbox.l)}_p{prov.page_number}"

    @staticmethod
    def get_table_content(table: Dict[str, Any], only_text: bool = True) -> List[Any]:
        """
        Extracts content from a table structure.

        Args:
            table (Dict[str, Any]): The table element to process.
            only_text (bool): Whether to return only text content or the full cell data.

        Returns:
            List[Any]: A list of table contents, as text or objects.
        """
        table_elements = []
        for element in table.get("data", {}).get("table_cells", []):
            bbox = BBox.from_element_dictionary(element.get("bbox").copy())
            if bbox.coord_origin == "TOPLEFT":
                bbox = BoundingBoxUtils.recalculate_bbox_topleft2bottomleft(bbox)

            text = element.get("text")
            if only_text:
                table_elements.append(text)
            else:
                table_elements.append({"text": text, "prov": [{"bbox": bbox}]})
        return table_elements

    @staticmethod
    def set_chapter(current_chapter, hierarchy_level, text):
        """
        Updates the chapter string based on hierarchy level.

        Args:
            current_chapter (str): Current chapter structure.
            hierarchy_level (int): Level of the current heading.
            text (str): The heading text.

        Returns:
            str: The updated chapter string.
        """
        if not current_chapter:
            current_chapter = text
        else:
            parts = current_chapter.split(";;")
            # Wenn aktuelle Tiefe existiert → ersetzen
            if hierarchy_level < len(parts):
                parts[hierarchy_level] = text
                # Alles untergeordnete löschen
                parts = parts[: hierarchy_level + 1]
            # Wenn neue Tiefe → anhängen
            elif hierarchy_level == len(parts):
                parts.append(text)
            # Falls Tiefe übersprungen wurde (unüblich), auffüllen mit Dummy
            else:
                while len(parts) < hierarchy_level:
                    parts.append("[UNDEFINED]")
                parts.append(text)

            current_chapter = ";;".join(parts)
        return current_chapter


class PDFContentGetter:
    """
    Helper class for retrieving document content from local JSON files or a remote server.
    """

    @staticmethod
    def get_content_from_json(json_filepath: str) -> List[str]:
        """
        Loads content from a local JSON file.

        Args:
            json_filepath (str): Path to the JSON file.

        Returns:
            List[str]: List of lines or elements in the document.
        """
        with open(json_filepath, "r", encoding="utf-8") as json_file:
            parsed_json = json.load(json_file)
        return parsed_json

    @staticmethod
    def get_content_from_docling_server(file_path: str) -> List[str]:
        """
        Sends a file to the Docling server and retrieves the parsed content.

        Args:
            file_path (str): Path to the file to send.

        Returns:
            List[str]: List of lines or elements returned by the server.
        """
        res = send_request(
            "http://10.100.100.12:5001", "app.tools.docling", "alice", file=file_path
        )
        if res.status_code != 200:
            raise RuntimeError(
                f"""Failed to retrieve content from Docling server.
                Status code: {res.status_code}, Response: {res.text}"""
            )
        returning_json = json.loads(res.text)
        return returning_json


# Main Application
class PDFIngestApplication:
    """
    Main application for processing PDF documents and splitting them into sections.
    """

    def __init__(self):
        """
        Initializes the application with a database client.
        """

    @staticmethod
    def run(input_file: str):
        """
        Runs the processing on the given input PDF file.

        Args:
            input_file (str): Path to the input PDF file.
        """
        # doc = TechnicalDocumentation(input_file)

        parsed_json = PDFContentGetter.get_content_from_docling_server(input_file)
        sections = SectionProcessor.split_elements_by_section(parsed_json)
        return sections


if __name__ == "__main__":
    # output_path = cutout("pdf_processing/documents/54530_hdb_de_12.pdf", 39, 39)
    # app = PDFIngestApplication(client)
    # app.run(output_path)
    OUTPUT_PATH = "pdf_processing/documents/54530_hdb_de_12_39_39.pdf"
    content = PDFContentGetter.get_content_from_docling_server(OUTPUT_PATH)
    with open("parsedjson_page39.json", "w", encoding="utf-8") as output_file:
        json.dump(content, output_file, indent=4)
