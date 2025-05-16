# from jira_tools.attachement_handler import ImageExtractor, PDFExtractor, handlers
# from file_processing.document_types import get_file_object

# doc = get_file_object(
#     'tmp/fileblobs/DATA-47_image-20241114-140519.png'
# )

# extension = doc.get_file_extension()
# if extension not in handlers:
#     print(f"No handler found for file type: {extension}. Skipping attachment.")
#     exit()

# extractor = ImageExtractor(doc)

# print(extractor.extract(base_path='tmp/fileblobs'))

from agent_utils import keyword_search, better_keyword_search

# res = keyword_search("test", "description", match_mode="fuzzy", fuzzy_threshold=65)
res = keyword_search("test", category="description", match_mode="contains")
for i in res:
    print(f"=== {i.key} ===")
    print(f"Summary: {i.summary}")
    print(f"Description: {i.description}")
    print("=== END ===\n")