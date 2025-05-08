from jira_tools.attachement_handler import ImageExtractor, PDFExtractor, handlers
from file_processing.document_types import get_file_object

doc = get_file_object(
    'tmp/fileblobs/DATA-47_image-20241114-140519.png'
)

extension = doc.get_file_extension()
if extension not in handlers:
    print(f"No handler found for file type: {extension}. Skipping attachment.")
    exit()

extractor = ImageExtractor(doc)

print(extractor.extract(base_path='tmp/fileblobs'))