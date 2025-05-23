"""
__version__ = "1.0.0"
__author__ = "Patrick Scheich"
__date__ = datetime.now().strftime("%Y-%m-%d")
"""

import string
from copy import deepcopy
from pydantic import BaseModel, PrivateAttr
from typing import Dict, Any
from datetime import datetime


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
        "supervisor_agent": "You are a supervisor agent orchestrating multiple specialized agents to gather, monitor, and summarize information efficiently.",
        "translator": "You are a professional translator specialized in technical and domain-specific texts, maintaining accuracy and clarity.",
        "reviewer": "You are a meticulous content reviewer focused on identifying inconsistencies and improving clarity.",
        "python_software_engineer": "You are a software engineer with expertise in Python and data science, capable of writing and reviewing code.",
        "expert_software_architect": "You are an expert software architect with deep knowledge of software design, architectural patterns, and best practices in software engineering."
    }

    TASK = {
        "describe": {
            "role_key": "content_expert",
            "template": "Describe the {object} in a way that is optimized for {recipient}. Format your response {format}.",
        },
        "summarize": {
            "role_key": "content_expert",
            "template": "Summarize the {object} for {recipient}, highlighting the most relevant information for {purpose}.",
        },
        "extract": {
            "role_key": "extractor",
            "template": "Extract the key information from the {object} relevant to {goal}, output it in {format} format.",
        },
        "keyword_extraction": {
            "role_key": "extractor",
            "template": "From the {object}, extract a list of relevant keywords suitable for {recipient}. {context} Return the result {format} optimized for {goal}.",
        },
        "jira_support": {
            "role_key": "jira_expert",
            "template": "Respond to questions about {object} with high information density, focusing on {goal}. Provide {detail_level} explanations to {recipient}. {context}",
        },
        "translate": {
            "role_key": "translator",
            "template": "Translate the {object} from {source_language} to {target_language} maintaining technical accuracy and clarity for {recipient}.",
        },
        "code_review": {
            "role_key": "python_software_engineer",
            "template": "Perform a code review of the {object}, focusing on {goal}. Provide actionable suggestions optimized for {recipient}. Return the result in {format}.",
        },
        "optimize_code_professional": {
            "role_key": "expert_software_architect",
            "template": "Optimize the {object} to a professional level. {context} Focus on {goal}. Provide the refactored code {format}.",
        },
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
        "jira_integration": "JIRA integration with other development and collaboration tools",
        "code_snippet": "source code snippet",
        "user_manual": "user manual or guide",
        "meeting_notes": "meeting notes or minutes",
        "product_specification": "product specification document",
        "translator_team": "a professional translation team requiring domain-specific terminology",
        "review_team": "a quality assurance team focused on document accuracy and clarity",
    }

    RECIPIENT = {
        "ai_model": "an AI model Processor for further analysis",
        "end_user": "a non-technical end user for better understanding",
        "search_index": "a semantic search index for optimized retrieval",
        "keyword_extractor": "exact keyword matching (e.g. 'if word in text')",
        "jira_beginner": "an user who is new to JIRA and needs foundational explanations with minimal jargon.",
        "jira_intermediate": "an user who has working knowledge of JIRA but may need clarification on advanced features.",
        "jira_advanced": "a JIRA administrator or power user who needs sophisticated technical insights.",
        "code": "a professional coding project with high standards of clarity, reusability and maintainability",
        "junior_developer": "a junior developer to guide them in improving their coding skills",
        "senior_developer": "a senior developer for a critical peer review, focusing on architectural implications and complex logic",
        "lead_developer": "a lead developer for final approval, ensuring alignment with project standards and long-term vision",
        "code_base_integrator": "a developer responsible for integrating the optimized code into an existing codebase",
    }

    FORMAT = {
        "contextual_search": "as a list of relevant items for contextual retrieval (do not use code blocks or markdown formatting)",
        "structured_data": "as a list of structured data items (do not use code blocks or markdown formatting)",
        "summary": "as a concise summary (do not use code blocks or markdown formatting)",
        "string_list": "as a plain list of strings, separated by commas or line breaks, without any code blocks or markdown formatting",
        "markdown": "formatted in markdown for readability",
        "json": "as JSON structured data",
        "plain_text": "as plain text without formatting",
        "code": "as a fully optimized code snippet, ready for direct integration, with comments explaining significant changes",
    }

    PURPOSE = {
        "training": "fine-tuning a language model",
        "retrieval": "improving search accuracy",
        "human_reading": "human readability",
        "reporting": "preparing information for reporting purposes",
        "translation": "translation accuracy and fidelity",
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
        "quality_assurance": "quality assurance and error detection",
        "workflow_optimization": "workflow optimization and process improvement",
        "code": "robust, reusable, expandable code",
        "code_quality": "code quality, adherence to best practices, and potential for bugs",
        "performance_optimization": "performance bottlenecks and opportunities for optimization",
        "security_vulnerabilities": "security vulnerabilities and potential exploits",
        "maintainability_scalability": "maintainability, readability, and scalability",
        "architectural_soundness": "architectural soundness and adherence to established software architecture principles",
        "design_pattern_application": "correct and idiomatic application of relevant design patterns",
        "best_practice_adherence": "adherence to industry best practices for robust and clean code",
        "refactoring_for_clarity": "refactoring for improved clarity, simplicity, and elegance",
    }

    CONTEXT = {
        "none": "",
        "relevance_explanation": "\"Relevant\" in this context means the most important topics or entities mentioned excluding common words and generic terms (e.g. 'task', 'thing', 'item', 'element').",
        "number_limit": "Limit the number of keywords to between {min_keywords} and {max_keywords}.",
        "no_generic_terms": "Focus only on content-carrying terms. Exclude generic or context-free words such as 'task', 'thing', 'item', or 'process'.",
        "exact_information": "Provide exact information without any additional context or explanation.",
        "high_information_density": "Provide high information density, focusing on the most relevant details.",
        "confidentiality_reminder": "Remember to exclude any confidential or sensitive information.",
        "format_instructions": "Follow strict formatting guidelines as per the recipient's requirements.",
        "common_software_patterns": "Apply widely accepted software design patterns (e.g., Singleton, Factory, Strategy, Observer) and architectural patterns (e.g., MVC, Microservices, Layered Architecture).",
        "clean_code_principles": "Apply principles of clean code (e.g., meaningful names, functions that do one thing, no duplication).",
        "solid_principles_applied": "Ensure adherence to SOLID principles (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion).",
        "dry_principle_applied": "Adhere to the DRY (Don't Repeat Yourself) principle.",
        "idiomatic_code_style": "Ensure the code adheres to idiomatic practices and coding style for the given programming language.",
        "performance_considerations": "Consider performance implications and optimize where necessary.",
        "security_considerations": "Review for and mitigate potential security vulnerabilities.",
        "readability_maintainability": "Prioritize readability, maintainability, and scalability.",
    }

    DETAIL_LEVEL = {
        "concise": "concise",
        "detailed": "comprehensive",
        "step_by_step": "step-by-step",
        "high_level": "high-level overview",
    }

    @staticmethod
    def _extract_placeholders(template: str) -> set:
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

        params.setdefault("context", "none")
        required_keys = cls._extract_placeholders(template)

        combined_params = {}
        for key in required_keys:
            try:
                # Neue Validierungslogik
                value = cls._resolve_value(key, params)
                combined_params[key] = value
            except KeyError as e:
                raise ValueError(
                    f"Required parameter '{key}' is missing and no 'none' fallback is available.\n" 
                    f"Consider one of the following: \n{',\n'.join(PromptStore.get_key_values(key))}"
                ) from e

        base_prompt = f"{role} {template.format(**combined_params)}"
        return cls._recursive_format(base_prompt, params)

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
            if "none" in lookup_dict:
                return lookup_dict["none"]
            raise KeyError(
                f"Parameter '{key}' not provided and no 'none' fallback in {key.upper()}"
            )

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
            
            # Verbesserte Formatierung für Listen: Komma und 'und'
            if len(resolved_items) == 1:
                return resolved_items[0]
            elif len(resolved_items) == 2:
                return f"{resolved_items[0]} and {resolved_items[1]}"
            elif len(resolved_items) > 2:
                return f"{', '.join(resolved_items[:-1])}, and {resolved_items[-1]}"
            return ""

        return lookup_dict.get(value, params.get(value, value))

    @classmethod
    def _recursive_format(
        cls, text: str, params: dict, seen_keys: set = None
    ) -> str:
        """
        Recursively format a string with parameters, resolving nested placeholders using path-based cycle detection.

        Args:
            text (str): The text to format.
            params (dict): The dictionary of parameters for formatting.
            seen_keys (set): Set of keys that are currently in the formatting path to detect cycles.

        Returns:
            str: The fully resolved string.

        Raises:
            ValueError: If a cyclic reference is detected.
        """
        seen_keys = seen_keys or set()
        placeholders = cls._extract_placeholders(text)

        if not placeholders:
            return text

        resolved_params = {}

        for key in placeholders:
            if key in seen_keys:
                raise ValueError(f"Cyclic reference detected for placeholder: '{key}'")
            seen_keys.add(key)
            value = cls._resolve_value(key, params)
            if isinstance(value, str) and "{" in value:
                value = cls._recursive_format(value, params, seen_keys.copy())
            resolved_params[key] = value
            seen_keys.remove(key)

        return text.format(**resolved_params)


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
    def get_all_template_keys(cls, only_key=True) -> dict:
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
            return [
                key.lower()
                for key in cls.__dict__.keys()
                if isinstance(cls.__dict__[key], dict) and not key.startswith("__")
            ]
        
    @classmethod
    def get_key_values(cls, key: str, only_keys=True) -> list:
        """
        Get all available values for a specific key in the template dictionaries.

        Args:
            key (str): The name of the key to retrieve values for.

        Returns:
            list: A list of all available values for the specified key.

        Raises:
            ValueError: If the specified key does not correspond to a valid template dictionary.
        """
        template_dict = getattr(cls, key.upper(), None)
        if not isinstance(template_dict, dict):
            raise ValueError(f"'{key}' is not a valid template dictionary.")
        if only_keys:
            return list(template_dict.keys())
        else:
            return list({"key": key, "value": value} for key, value in template_dict.items())


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
    
    def get_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all configurations.

        Returns:
            Dict[str, Dict[str, Any]]: The complete dictionary of prompt configurations.
        """
        return self._configs
    
    def get_keys(self, only_keys=True) -> list:
        """
        Get all available keys for the prompt configurations.

        Args:
            only_keys (bool): If True, return only the keys of the prompt configurations.

        Returns:
            list: A list of all available keys or a dictionary of key-value pairs.
        """
        return list(self._configs.keys())

prompt_configs = PromptConfig(
    {
        "keyword_extraction": {
            "object": "text",
            "format": "string_list",
            "recipient": "keyword_extractor",
            "goal": "exact_matching",
            "context": ["relevance_explanation", "no_generic_terms", "number_limit"],
            "min_keywords": 3,
            "max_keywords": 5,
        },
        "describe": {
            "object": "image",
            "format": "contextual_search",
            "recipient": "ai_model",
        },
        "refine_code": {
            "object": "code_snippet",
            "format": "markdown",
            "recipient": "senior_developer",
            "goal": ["code_quality", "maintainability_scalability", "performance_optimization"],
        },
        "professional_code_optimization": {
            "object": "code_snippet",
            "format": "code",
            "context": ["clean_code_principles", "solid_principles_applied", "dry_principle_applied", "idiomatic_code_style", "common_software_patterns", "performance_considerations", "security_considerations", "readability_maintainability"],
            "goal": ["architectural_soundness", "design_pattern_application", "best_practice_adherence", "refactoring_for_clarity"],
        },
    }
)


if __name__ == "__main__":

    def main():
        # object_keys = PromptStore.get_key_values("object")
        # print(object_keys)
        prompt = PromptStore.get_prompt(
            "describe",
            recipient="ai_model",
            object="image",
            format="contextual_search",
        )

        prompt = PromptStore.get_prompt(
            "code_review",
            **prompt_configs.get("refine_code"),
        )

        professional_optimization_prompt = PromptStore.get_prompt(
            "optimize_code_professional",
            **prompt_configs.get("professional_code_optimization"),
        )
        print("\n--- Professional Code Optimization Prompt ---")
        print(professional_optimization_prompt)
        print(prompt)
        # print(PromptStore.get_keys("describe"))
        # print(PromptStore.get_all_template_keys(only_key=False))

        # prompt = PromptStore.get_prompt(
        #     "keyword_extraction",
        #     **prompt_configs.get("keyword_extraction", max_keywords=3),
        # )
        # print(prompt)

    main()