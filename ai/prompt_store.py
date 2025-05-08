import string


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
        "extractor": "You are an information extraction tool optimized for structured output."
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
        }
    }

    OBJECT = {
        "image": "provided image",
        "document": "uploaded document",
        "text": "given text"
    }

    RECIPIENT = {
        "ai_model": "an AI model Processor for further analysis",
        "end_user": "a non-technical end user for better understanding",
        "search_index": "a semantic search index for optimized retrieval"
    }

    FORMAT = {
        "contextual_search": "so it can be effectively indexed for contextual retrieval",
        "structured_data": "as structured JSON for further processing",
        "summary": "as a concise summary"
    }

    PURPOSE = {
        "training": "fine-tuning a language model",
        "retrieval": "improving search accuracy",
        "human_reading": "human readability"
    }

    GOAL = {
        "metadata_tagging": "metadata tagging",
        "semantic_indexing": "semantic indexing",
        "classification": "automated classification"
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
        Builds a prompt using the template identified by `prompt_name` and formats it with given parameters.

        Args:
            prompt_name (str): The name of the task prompt to retrieve.
            **params: Parameters to fill the prompt placeholders.

        Returns:
            str: The formatted prompt string.

        Raises:
            ValueError: If required parameters are missing or placeholders can't be resolved.
        """

        # Step 1: Get task template
        task = cls.TASK.get(prompt_name)
        if not task:
            raise ValueError(f"Prompt '{prompt_name}' not found in TASK store.")

        # Step 2: Get role for the task
        role_key = task.get("role_key")
        role = cls.ROLE.get(role_key, "")  # Fallback to an empty string if the role is not found
        
        # Step 3: Get template
        template = task.get("template")
        if not template:
            raise ValueError(f"Template for task '{prompt_name}' is missing.")
        
        # Step 4: Extract required keys dynamically
        required_keys = cls._extract_placeholders(template)

        # Step 5: Validate all required keys are provided
        missing_keys = [
            key for key in required_keys if key not in params or not params[key]
        ]
        if missing_keys:
            raise ValueError(
                f"Missing required parameter(s): {', '.join(missing_keys)}"
            )

        # Step 6: Fill parameters using mapping dictionaries if defined
        filled_params = {}
        for key in required_keys:
            value = params[key]
            lookup_dict = getattr(cls, key.upper(), {})
            filled_params[key] = (
                lookup_dict.get(value, value)
                if isinstance(lookup_dict, dict)
                else value
            )

        # Step 7: Format and return prompt, including role at the beginning
        try:
            return f"{role} {template.format(**filled_params)}"
        except KeyError as e:
            raise ValueError(
                f"Placeholder '{e.args[0]}' could not be resolved with parameters."
            ) from e
        
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


if __name__ == "__main__":
    prompt = PromptStore.get_prompt(
        "describe",
        recipient="ai_model",
        object="image",
        format="contextual_search",
    )
    print(prompt)
    print(PromptStore.get_keys("describe"))
    print(PromptStore.get_available_template_keys("recipient"))
    print(PromptStore.get_all_template_keys())
