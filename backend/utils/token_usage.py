def get_token_usage(result):
    """Parse and return token usage from API response."""
    usage = result.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)
    token_usage=f"""
        Prompt: {prompt_tokens},
        Completion: {completion_tokens},
        Total: {total_tokens}
        """
    return token_usage, total_tokens