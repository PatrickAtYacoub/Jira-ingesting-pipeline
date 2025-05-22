from typing import List, Literal
import re
from ai import PromptStore, prompt_configs, prompt
from model import JiraBaseIssue
from jira_tools import JiraHandler
from rapidfuzz import fuzz
from lib.logger import agent_logger as logger
import time


def keyword_search(
    query: str,
    category: List[str] = ["summary", "description"],
    match_mode: Literal["strict", "fuzzy", "contains"] = "contains",
    fuzzy_threshold: int = 85,
) -> List[JiraBaseIssue]:
    """
    Searches Jira issues based on extracted keywords and matches them 
    using either strict or fuzzy matching against specified text fields.

    Args:
        query (str): The natural-language input from which keywords are extracted.
        category (List[str]): The attributes of the Jira issue to search in 
                              (e.g., ["summary", "description"]). Defaults to ["summary", "description"].
        match_mode (Literal["strict", "fuzzy", "contains"]): 
            - "strict": Exact keyword match (word boundary-based, case-insensitive).
            - "fuzzy": Token-level fuzzy matching using a similarity threshold.
            - "contains": Substring match.
        fuzzy_threshold (int): Minimum similarity ratio (0–100) required for fuzzy matching. 
                               Only used if match_mode is "fuzzy". Defaults to 85.

    Returns:
        List[JiraBaseIssue]: A list of Jira issues matching all extracted keywords
                             under the specified matching strategy.
    """

    def get_keywords(text: str) -> List[str]:
        """
        Extracts key terms from the input text using a prompt-based LLM extraction.

        Args:
            text (str): The query text from which to extract keywords.

        Returns:
            List[str]: A list of keywords extracted from the query.
        """

        amount_of_sentences = len(re.findall(r"[.!?]", text))
        if amount_of_sentences == 0:
            amount_of_sentences = 1

        prompt_template = PromptStore.get_prompt(
            "keyword_extraction",
            **prompt_configs.get("keyword_extraction", min_keywords = amount_of_sentences + 1, max_keywords=2 * amount_of_sentences)
        )
        return [kw.strip() for kw in prompt(system_prompt=prompt_template, user_prompt=text).split(",")]

    def is_token_fuzzy_match(text: str, keyword: str, threshold: int = 85) -> bool:
        """
        Performs token-level fuzzy matching between a keyword and all words in the text.

        Args:
            text (str): The text to search in.
            keyword (str): The keyword to match.
            threshold (int): Similarity threshold between 0 and 100.

        Returns:
            bool: True if the keyword approximately matches any token in the text.
        """
        tokens = re.findall(r"\b\w[\w-]*\b", text.lower())
        return any(fuzz.ratio(keyword.lower(), token) >= threshold for token in tokens)

    def is_match(text: str, keyword: str) -> bool:
        """
        Applies either strict or fuzzy matching between keyword and given text.

        Args:
            text (str): The content to search in (e.g., issue summary).
            keyword (str): The keyword to check against the text.

        Returns:
            bool: True if the keyword matches the text according to the selected match mode.
        """
        if match_mode == "strict":
            return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text, flags=re.IGNORECASE) is not None
        elif match_mode == "fuzzy":
            return is_token_fuzzy_match(text, keyword, fuzzy_threshold)
        elif match_mode == "contains":
            return keyword.lower() in text.lower()
        else:
            raise ValueError(f"Unknown match_mode: {match_mode}")

    keywords = get_keywords(query)
    logger.debug(f"Extracted keywords: {keywords}")
    hdlr = JiraHandler()
    start = time.time()
    issues = hdlr.fetch_and_parse_issues(jql="project=DATA")
    stop = time.time()
    logger.debug(f"Fetched issues in {stop - start:.2f} seconds")

    return [
        issue for issue in issues
        if all(
            any(is_match(getattr(issue, cat, ""), kw) for cat in category)
            for kw in keywords
        )
    ]


from typing import List, Literal
from jira_tools import JiraHandler
from rapidfuzz import fuzz
import re
# import nltk
# from nltk.corpus import stopwords
# from nltk.tokenize import word_tokenize

# from keybert import KeyBERT

# nltk.download('stopwords')
# nltk.download('punkt_tab')

def better_keyword_search(
    query: str,
    category: List[str] = ["summary", "description"],
    match_mode: Literal["strict", "fuzzy", "contains"] = "contains",
) -> List["JiraBaseIssue"]:
    
    kw_model = None#KeyBERT()
    # Extrahiere relevante Phrasen (1- bis 3-gram) mit Stoppwortfilter
    extracted_keywords = kw_model.extract_keywords(
        query,
        keyphrase_ngram_range=(1, 2),
        stop_words="english", 
        use_maxsum=True,
        nr_candidates=10,
        top_n=3
    )
    
    keywords = [kw for kw, _ in extracted_keywords]
    logger.debug(f"Extracted keywords with KeyBERT: {keywords}")

    # Baue die JQL-Query
    jql_query = "project=DATA AND ("
    for i, keyword in enumerate(keywords):
        # Erlaube Phrasen mit Anführungszeichen in JQL
        if match_mode == "strict":
            jql_query += f"({' OR '.join([f'{field} ~ \"\\\"{keyword}\\\"\"' for field in category])})"
        else:  # fuzzy & contains behandeln wir gleich
            jql_query += f"({' OR '.join([f'{field} ~ \"{keyword}\"' for field in category])})"
        if i < len(keywords) - 1:
            jql_query += " AND "
    jql_query += ")"

    logger.debug(f"Generated JQL query: {jql_query}")

    # Führe die Suche mit deinem Jira-Handler aus
    hdlr = JiraHandler()
    return hdlr.fetch_and_parse_issues(jql=jql_query)