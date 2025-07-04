from typing import Any, Dict, List
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage


def get_research_topic(messages: List[AnyMessage]) -> str:
    """
    Get the research topic from the messages.
    """
    # check if request has a history and combine the messages into a single string
    if len(messages) == 1:
        research_topic = messages[-1].content
    else:
        research_topic = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                research_topic += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                research_topic += f"Assistant: {message.content}\n"
    return research_topic


def resolve_urls(urls_to_resolve: List[Any], id: int) -> Dict[str, str]:
    """
    Create a map of the search urls (very long) to a short url with a unique id for each url.
    Ensures each original URL gets a consistent shortened form while maintaining uniqueness.
    """
    prefix = f"https://search.deepseek.com/id/"
    
    # Handle different URL formats for DeepSeek
    urls = []
    for site in urls_to_resolve:
        if hasattr(site, 'web') and hasattr(site.web, 'uri'):
            urls.append(site.web.uri)
        elif isinstance(site, str):
            urls.append(site)
        elif isinstance(site, dict) and 'url' in site:
            urls.append(site['url'])

    # Create a dictionary that maps each unique URL to its first occurrence index
    resolved_map = {}
    for idx, url in enumerate(urls):
        if url not in resolved_map:
            resolved_map[url] = f"{prefix}{id}-{idx}"

    return resolved_map


def insert_citation_markers(text, citations_list):
    """
    Inserts citation markers into a text string based on start and end indices.

    Args:
        text (str): The original text string.
        citations_list (list): A list of dictionaries, where each dictionary
                               contains 'start_index', 'end_index', and
                               'segment_string' (the marker to insert).
                               Indices are assumed to be for the original text.

    Returns:
        str: The text with citation markers inserted.
    """
    # Sort citations by end_index in descending order.
    # If end_index is the same, secondary sort by start_index descending.
    # This ensures that insertions at the end of the string don't affect
    # the indices of earlier parts of the string that still need to be processed.
    sorted_citations = sorted(
        citations_list, key=lambda c: (c["end_index"], c["start_index"]), reverse=True
    )

    modified_text = text
    for citation_info in sorted_citations:
        # These indices refer to positions in the *original* text,
        # but since we iterate from the end, they remain valid for insertion
        # relative to the parts of the string already processed.
        end_idx = citation_info["end_index"]
        marker_to_insert = ""
        for segment in citation_info["segments"]:
            marker_to_insert += f" [{segment['label']}]({segment['short_url']})"
        # Insert the citation marker at the original end_idx position
        modified_text = (
            modified_text[:end_idx] + marker_to_insert + modified_text[end_idx:]
        )

    return modified_text


def get_citations(response, resolved_urls_map):
    """
    Extracts and formats citation information from a DeepSeek model's response.

    This function processes the DeepSeek response to construct a list of citation objects.
    Each citation object includes the start and end indices of the text segment it refers to,
    and a string containing formatted markdown links to the supporting sources.

    Args:
        response: The response object from the DeepSeek model.
                  It also relies on a `resolved_map` being available in its
                  scope to map URLs to resolved short URLs.

    Returns:
        list: A list of dictionaries, where each dictionary represents a citation
              and has the following keys:
              - "start_index" (int): The starting character index of the cited
                                     segment in the original text. Defaults to 0
                                     if not specified.
              - "end_index" (int): The character index immediately after the
                                   end of the cited segment (exclusive).
              - "segments" (list[str]): A list of individual markdown-formatted
                                        links for each source.
              Returns an empty list if no valid response is found.
    """
    citations = []

    # Ensure response is present
    if not response:
        return citations

    # For DeepSeek, create a simplified citation structure
    # This is a basic implementation - you may need to adjust based on actual response format
    citation = {
        "start_index": 0,
        "end_index": len(response.content) if hasattr(response, 'content') else 0,
        "segments": [{
            "label": "DeepSeek Research",
            "short_url": resolved_urls_map.get("deepseek_research", "deepseek_research"),
            "value": "DeepSeek research result"
        }]
    }
    
    citations.append(citation)
    return citations
