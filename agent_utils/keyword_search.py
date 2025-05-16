from typing import List, Literal
import re
from ai import PromptStore, prompt_configs, prompt
from model import JiraBaseIssue
from jira_tools import JiraHandler
from rapidfuzz import fuzz


def keyword_search(
    query: str,
    category: str = "summary",
    match_mode: Literal["strict", "fuzzy", "contains"] = "strict",
    fuzzy_threshold: int = 85,
) -> List[JiraBaseIssue]:
    """
    Searches Jira issues based on extracted keywords and matches them 
    using either strict or fuzzy matching against a specified text field.

    Args:
        query (str): The natural-language input from which keywords are extracted.
        category (str): The attribute of the Jira issue to search in 
                        (e.g., "summary", "description"). Defaults to "summary".
        match_mode (Literal["strict", "fuzzy"]): 
            - "strict": Exact keyword match (word boundary-based, case-insensitive).
            - "fuzzy": Token-level fuzzy matching using a similarity threshold.
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
        prompt_template = PromptStore.get_prompt(
            "keyword_extraction",
            **prompt_configs.get("keyword_extraction", max_keywords=3)
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
    hdlr = JiraHandler()
    issues = hdlr.fetch_and_parse_issues(jql="project=DATA")

    return [
        issue for issue in issues
        if all(is_match(getattr(issue, category, ""), kw) for kw in keywords)
    ]


from typing import List, Literal
from jira_tools import JiraHandler
from rapidfuzz import fuzz
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# nltk.download('stopwords')
# nltk.download('punkt_tab')

def better_keyword_search(
    query: str,
    category: str = ["summary", "description"],
    match_mode: Literal["strict", "fuzzy", "contains"] = "fuzzy",
    fuzzy_threshold: int = 85,
) -> List[JiraBaseIssue]:

    stop_words = set(stopwords.words('english'))  # Oder andere Sprache
    keywords = [word for word in word_tokenize(query) if word.lower() not in stop_words and word.isalnum()]

    jql_query = "project=DATA AND ("
    for i, keyword in enumerate(keywords):
        if match_mode == "strict":
            jql_query += f"({' OR '.join([f'{field} ~ "{keyword}"' for field in category])})"
        elif match_mode == "fuzzy" or match_mode == "contains":
            jql_query += f"({' OR '.join([f'{field} ~ "{keyword}"' for field in category])})"
        if i < len(keywords) - 1:
            jql_query += " AND "
    jql_query += ")"

    hdlr = JiraHandler()
    return hdlr.fetch_and_parse_issues(jql=jql_query)
