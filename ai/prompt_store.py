import string
from copy import deepcopy
from pydantic import BaseModel, PrivateAttr
from typing import Dict, Any


class PromptStore:
    """
    prompt_store.py
    ===============
    This module defines the `PromptStore` class. It serves as a centralized repository for managing and generating prompts used in AI interactions.
    The class provides methods to retrieve and format prompts based on predefined templates and dynamic parameters.
    It also includes functionality to extract placeholder names from templates and validate the presence of required parameters.
    If the value for a key is not found in the mapping dictionary, it will be used as is.
    """

    ROLE = {
        "content_expert": "You are a helpful assistant specialized in content understanding.",
        "python_senior": "You are an experienced Python Senior Developer who is specialized in data science.",
        "extractor": "You are an information extraction tool optimized for structured output.",
        "jira_expert": "You are a JIRA expert with deep knowledge of Atlassian products, agile methodologies and project management best practices. You understand how to optimize workflows, create effective tickets, and manage project resources efficiently.",
    }

    TASK = {
        "describe": {
            "role_key": "content_expert",
            "template": "Describe the {object} in a way that is optimized for {recipient}. Format your response {format}."
        },
        "summarize": {
            "role_key": "content_expert",
            "template": "Summarize the {object} for {recipient}, highlighting the most relevant information for {purpose}."
        },
        "extract": {
            "role_key": "extractor",
            "template": "Extract the key information from the {object} relevant to {goal}, output it in {format} format."
        },
        "keyword_extraction": {
            "role_key": "extractor",
            "template": "From the {object}, extract a list of relevant keywords suitable for {recipient}. {context}Return the result {format} optimized for {goal}."
        },
        "jira_support": {
            "role_key": "jira_expert",
            "template": "Respond to questions about {object} with high information density, focusing on {goal}. Provide {detail_level} explanations to {recipient}. {context}"
        }

    }

    OBJECT = {
        "image": "provided image",
        "document": "uploaded document",
        "text": "given text",
        "jira_general": "JIRA fundamentals, concepts, and best practices",
        "jira_workflows": "JIRA workflow configuration, states, transitions, and automation",
        "jira_queries": "JQL (JIRA Query Language) syntax, filters, and search strategies",
        "jira_boards": "Sprint, Kanban, and Scrum board configuration and management",
        "jira_automation": "JIRA automation rules, triggers, and integration capabilities",
        "jira_reporting": "JIRA reporting, dashboards, and metrics analysis",
        "jira_integration": "JIRA integration with other development and collaboration tools"
    }

    RECIPIENT = {
        "ai_model": "an AI model Processor for further analysis",
        "end_user": "a non-technical end user for better understanding",
        "search_index": "a semantic search index for optimized retrieval",
        "keyword_extractor": "exact keyword matching (e.g. 'if word in text')",
        "jira_beginner": "an user who is new to JIRA and needs foundational explanations with minimal jargon.",
        "jira_intermediate": "an user who has working knowledge of JIRA but may need clarification on advanced features.",
        "jira_advanced": "a JIRA administrator or power user who needs sophisticated technical insights."
    }

    FORMAT = {
        "contextual_search": "as a list of relevant items for contextual retrieval (do not use code blocks or markdown formatting)",
        "structured_data": "as a list of structured data items (do not use code blocks or markdown formatting)",
        "summary": "as a concise summary (do not use code blocks or markdown formatting)",
        "string_list": "as a plain list of strings, separated by commas or line breaks, without any code blocks or markdown formatting"
    }

    PURPOSE = {
        "training": "fine-tuning a language model",
        "retrieval": "improving search accuracy",
        "human_reading": "human readability"
    }

    GOAL = {
        "metadata_tagging": "metadata tagging",
        "semantic_indexing": "semantic indexing",
        "classification": "automated classification",
        "exact_matching": "exact keyword matching",
        "practical_solutions": "actionable recommendations and practical solutions",
        "technical_details": "technical implementation details and configuration steps",
        "strategic_guidance": "strategic guidance and best practices for enterprise-scale deployment",
        "efficiency_tips": "efficiency tips and productivity improvements",
        "comparison": "comparative analysis of different approaches or configurations",
        "information": "highly detailed information and insights",
    }

    CONTEXT = {
        "none": "",
        "relevance_explanation": "\"Relevant\" in this context means the most important topics or entities mentioned excluding common words and generic terms (e.g. 'task', 'thing', 'item', 'element').",
        "number_limit": "Limit the number of keywords to between {min_keywords} and {max_keywords}.",
        "no_generic_terms": "Focus only on content-carrying terms. Exclude generic or context-free words such as 'task', 'thing', 'item', or 'process'.",
        "exact_information": "Provide exact information without any additional context or explanation.",
        "high_information_density": "Provide high information density, focusing on the most relevant details."
    }

    DETAIL_LEVEL = {
        "concise": "concise",
        "detailed": "comprehensive",
        "step_by_step": "step-by-step"
    }

    @classmethod
    def _extract_placeholders(cls, template: str) -> set:
        """
        Extracts placeholder names from a format string.

        Args:
            template (str): The template string with placeholders.

        Returns:
            set: A set of placeholder names.
        """
        return {
            field_name
            for _, field_name, _, _ in string.Formatter().parse(template)
            if field_name
        }

    @classmethod
    def get_prompt(cls, prompt_name: str, **params) -> str:
        """
        Generate a prompt string based on the specified prompt name and parameters.

        Args:
            prompt_name (str): The name of the prompt/task to generate.
            **params: Arbitrary keyword arguments representing dynamic parameters for the prompt.

        Returns:
            str: The fully formatted prompt string.

        Raises:
            ValueError: If the prompt or required parameters are missing.
        """
        task = cls.TASK.get(prompt_name)
        if not task:
            raise ValueError(f"Prompt '{prompt_name}' nicht gefunden")

        role = cls.ROLE.get(task.get("role_key", ""), "")
        template = task.get("template", "")
        
        if not template:
            raise ValueError(f"Template für '{prompt_name}' fehlt")

        params.setdefault('context', 'none')
        required_keys = cls._extract_placeholders(template)
        
        combined_params = {}
        for key in required_keys:
            try:
                # Neue Validierungslogik
                value = cls._resolve_value(key, params)
                combined_params[key] = value
            except KeyError as e:
                raise ValueError(f"Required parameter '{key}' is missing and no 'none' fallback is available") from e

        base_prompt = f"{role} {template.format(**combined_params)}"
        return cls._recursive_format(base_prompt, params, max_depth=3)

    @classmethod
    def _resolve_value(cls, key: str, params: dict) -> str:
        """
        Resolve the value for a given key using the class-level mapping dictionaries and provided parameters.

        Args:
            key (str): The parameter key to resolve.
            params (dict): The dictionary of provided parameters.

        Returns:
            str: The resolved value for the key.

        Raises:
            KeyError: If the key is missing and no 'none' fallback is available.
            ValueError: If a list item cannot be resolved.
        """
        lookup_dict = getattr(cls, key.upper(), {})
        value = params.get(key, None)

        # None-Fallback Mechanismus
        if value is None:
            if 'none' in lookup_dict:
                return lookup_dict['none']
            raise KeyError(f"Parameter '{key}' not provided and no 'none' fallback in {key.upper()}")

        # Listenbehandlung mit erweiterter Validierung
        if isinstance(value, list):
            resolved_items = []
            for item in value:
                if item in lookup_dict:
                    resolved_items.append(str(lookup_dict[item]))
                elif item in params:
                    resolved_items.append(str(params[item]))
                else:
                    raise ValueError(f"Value '{item}' in list for '{key}' not found")
            return " ".join(resolved_items).strip()

        return lookup_dict.get(value, params.get(value, value))

    @classmethod
    def _recursive_format(
        cls, 
        text: str, 
        params: dict, 
        depth: int = 0, 
        max_depth: int = 3
    ) -> str:
        """
        Recursively format a string with parameters, resolving nested placeholders up to a maximum depth.

        Args:
            text (str): The text to format.
            params (dict): The dictionary of parameters for formatting.
            depth (int): The current recursion depth.
            max_depth (int): The maximum recursion depth allowed.

        Returns:
            str: The recursively formatted string.
        """
        if depth >= max_depth:
            return text

        placeholders = cls._extract_placeholders(text)
        if not placeholders:
            return text

        resolved_params = {
            p: cls._resolve_value(p, params)
            for p in placeholders
        }

        new_text = text.format(**resolved_params)
        
        if new_text == text:  # No changes made
            return text
        
        return cls._recursive_format(new_text, params, depth + 1, max_depth)
   
    @classmethod
    def get_keys(cls, prompt_name: str) -> set:
        """
        Get the keys required for a specific prompt.

        Args:
            prompt_name (str): The name of the task prompt.

        Returns:
            set: A set of required keys for the specified prompt.
        """
        task = cls.TASK.get(prompt_name)
        if not task:
            raise ValueError(f"Prompt '{prompt_name}' not found in TASK store.")
        
        template = task.get("template")
        if not template:
            raise ValueError(f"Template for task '{prompt_name}' is missing.")
        
        return cls._extract_placeholders(template)
    
    @classmethod
    def get_available_template_keys(cls, key: str) -> set:
        """
        Get all available keys of the specified template dictionary.

        Args:
            key (str): The name of the template dictionary (e.g., 'recipient').

        Returns:
            set: A set of all available keys in the specified template dictionary.

        Raises:
            ValueError: If the specified key does not correspond to a valid template dictionary.
        """
        template_dict = getattr(cls, key.upper(), None)
        if not isinstance(template_dict, dict):
            raise ValueError(f"'{key}' is not a valid template dictionary.")
        return set(template_dict.keys())
    
    @classmethod
    def get_all_template_keys(cls, only_key = True) -> dict:
        """
        Get all available template dictionaries.

        Args:
            only_key (bool): If True, return only the keys of the template dictionaries.
                If False, return the keys and their corresponding available keys.

        Returns:
            dict: A dictionary where keys are template dictionary names and values are sets of available keys.
        """
        if not only_key:
            return {
            key.lower(): set(value.keys())
            for key, value in cls.__dict__.items()
            if isinstance(value, dict) and not key.startswith("__")
            }
        else:
            return [key.lower() for key in cls.__dict__.keys() if isinstance(cls.__dict__[key], dict) and not key.startswith("__")]


class PromptConfig(BaseModel):
    """
    Helper class to manage prompt configurations with easy override and retrieval.

    Attributes:
        _configs (Dict[str, Dict[str, Any]]): Internal dictionary storing prompt configurations.
    """

    _configs: Dict[str, Dict[str, Any]] = PrivateAttr(default_factory=dict)

    def __init__(self, configs: Dict[str, Dict[str, Any]]):
        """
        Initialize PromptConfig with a dictionary of configurations.

        Args:
            configs (Dict[str, Dict[str, Any]]): Dictionary mapping prompt names to their configuration dictionaries.
        """
        self._configs = configs

    def get(self, name: str, **overrides) -> Dict[str, Any]:
        """
        Retrieve a configuration by name, applying any overrides.

        Args:
            name (str): The name of the prompt configuration to retrieve.
            **overrides: Key-value pairs to override in the configuration.

        Returns:
            Dict[str, Any]: The resulting configuration dictionary with overrides applied.
        """
        config = deepcopy(self._configs.get(name, {}))
        config.update(overrides)
        return config

prompt_configs = PromptConfig({
    "keyword_extraction": {
        "object": "text",
        "format": "string_list",
        "recipient": "keyword_extractor",
        "goal": "exact_matching",
        "context": ["relevance_explanation", "no_generic_terms", "number_limit"],
        "min_keywords": 3,
        "max_keywords": 5
    },
    "describe": {
        "object": "image",
        "format": "contextual_search",
        "recipient": "ai_model"
    },
})

if __name__ == "__main__":
    # prompt = PromptStore.get_prompt(
    #     "describe",
    #     recipient="ai_model",
    #     object="image",
    #     format="contextual_search",
    # )
    # print(prompt)
    # print(PromptStore.get_keys("describe"))
    # print(PromptStore.get_available_template_keys("recipient"))
    # print(PromptStore.get_all_template_keys())

    prompt = PromptStore.get_prompt(
    "keyword_extraction", 
    **prompt_configs.get("keyword_extraction", max_keywords=3)
    )
    print(prompt)
