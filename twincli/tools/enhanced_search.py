# twincli/tools/search.py
"""
Enhanced search tool with multiple strategies and persistence.

Category: research
Created: 2025-06-01
"""

import re
import time
from typing import List, Dict, Optional, Tuple
from twincli.tools.search import search_web
from twincli.tools.obsidian import search_obsidian


def intelligent_search(query: str, max_attempts: int = 5, include_obsidian: bool = True) -> str:
    """
    Performs intelligent, multi-strategy search that tries various approaches before giving up.
    
    Args:
        query: The search query
        max_attempts: Maximum number of search attempts to make
        include_obsidian: Whether to include Obsidian vault search
        
    Returns:
        Comprehensive search results or detailed failure analysis
    """
    results = []
    attempts = []
    
    # Strategy 1: Direct query search
    attempts.append("Direct query search")
    try:
        direct_result = search_web(query)
        if _is_good_result(direct_result, query):
            results.append(f"**Direct Search Results:**\n{direct_result}")
        else:
            results.append(f"**Direct Search (Limited Results):**\n{direct_result[:300]}...")
    except Exception as e:
        results.append(f"**Direct Search Failed:** {e}")
    
    # Strategy 2: Query refinement with keywords
    if len(results) == 0 or not _is_good_result(results[-1], query):
        attempts.append("Keyword-enhanced search")
        enhanced_query = _enhance_query_with_keywords(query)
        try:
            enhanced_result = search_web(enhanced_query)
            if _is_good_result(enhanced_result, query):
                results.append(f"**Enhanced Search Results ({enhanced_query}):**\n{enhanced_result}")
            else:
                results.append(f"**Enhanced Search (Limited):** {enhanced_query}\n{enhanced_result[:300]}...")
        except Exception as e:
            results.append(f"**Enhanced Search Failed:** {e}")
    
    # Strategy 3: Alternative phrasings
    if len(results) < 2 or not any(_is_good_result(r, query) for r in results):
        attempts.append("Alternative phrasing search")
        alt_queries = _generate_alternative_queries(query)
        for alt_query in alt_queries[:2]:  # Try top 2 alternatives
            try:
                alt_result = search_web(alt_query)
                if _is_good_result(alt_result, query):
                    results.append(f"**Alternative Search Results ({alt_query}):**\n{alt_result}")
                    break
                else:
                    results.append(f"**Alt Search (Limited):** {alt_query}\n{alt_result[:200]}...")
            except Exception as e:
                results.append(f"**Alt Search Failed ({alt_query}):** {e}")
    
    # Strategy 4: Component search (break down complex queries)
    if len(results) < 3 and " " in query:
        attempts.append("Component-based search")
        components = _extract_key_components(query)
        for component in components[:2]:  # Try top 2 components
            try:
                comp_result = search_web(component)
                if _is_good_result(comp_result, component):
                    results.append(f"**Component Search Results ({component}):**\n{comp_result}")
                    break
            except Exception as e:
                results.append(f"**Component Search Failed ({component}):** {e}")
    
    # Strategy 5: Obsidian vault search (if enabled)
    if include_obsidian:
        attempts.append("Obsidian vault search")
        try:
            obsidian_result = search_obsidian(query)
            if "Found" in obsidian_result and "notes containing" in obsidian_result:
                results.append(f"**Obsidian Vault Results:**\n{obsidian_result}")
            else:
                # Try key terms from query in Obsidian
                key_terms = _extract_key_terms(query)
                for term in key_terms[:2]:
                    term_result = search_obsidian(term)
                    if "Found" in term_result and "notes containing" in term_result:
                        results.append(f"**Obsidian Results ({term}):**\n{term_result}")
                        break
        except Exception as e:
            results.append(f"**Obsidian Search Failed:** {e}")
    
    # Strategy 6: Broader context search
    if len([r for r in results if _is_good_result(r, query)]) == 0:
        attempts.append("Broader context search")
        broader_query = _make_query_broader(query)
        try:
            broader_result = search_web(broader_query)
            results.append(f"**Broader Context Search ({broader_query}):**\n{broader_result}")
        except Exception as e:
            results.append(f"**Broader Search Failed:** {e}")
    
    # Compile final results
    good_results = [r for r in results if _is_good_result(r, query)]
    
    if good_results:
        summary = f"🔍 **Intelligent Search Results for: '{query}'**\n\n"
        summary += f"**Search Strategies Used:** {', '.join(attempts)}\n"
        summary += f"**Successful Results:** {len(good_results)}/{len(results)}\n\n"
        summary += "\n\n---\n\n".join(good_results)
        
        # Add analysis section
        summary += f"\n\n**Search Analysis:**\n"
        summary += f"- Attempted {len(attempts)} different search strategies\n"
        summary += f"- Found {len(good_results)} high-quality result sets\n"
        summary += f"- Most effective approach: {attempts[0] if good_results else 'None clearly successful'}\n"
        
        return summary
    else:
        # Detailed failure analysis
        failure_report = f"🔍 **Comprehensive Search Failed for: '{query}'**\n\n"
        failure_report += f"**Strategies Attempted:** {', '.join(attempts)}\n"
        failure_report += f"**Total Attempts:** {len(results)}\n\n"
        
        failure_report += "**Detailed Results:**\n"
        for i, result in enumerate(results, 1):
            failure_report += f"\n{i}. {result[:200]}{'...' if len(result) > 200 else ''}\n"
        
        failure_report += "\n**Recommendations:**\n"
        failure_report += "- Try rephrasing your query with different terminology\n"
        failure_report += "- Check if the topic might be very recent or specialized\n"
        failure_report += "- Consider breaking down complex queries into smaller parts\n"
        failure_report += f"- Alternative search terms to try: {', '.join(_generate_alternative_queries(query)[:3])}\n"
        
        return failure_report


def _is_good_result(result: str, original_query: str) -> bool:
    """Determine if a search result is high quality."""
    if not result or len(result) < 100:
        return False
    
    # Check for error indicators
    error_indicators = ["No results", "Error:", "Failed", "not found", "0 results"]
    if any(indicator.lower() in result.lower() for indicator in error_indicators):
        return False
    
    # Check for content quality indicators
    quality_indicators = ["http", "description", "snippet", "Found", "results for"]
    quality_score = sum(1 for indicator in quality_indicators if indicator.lower() in result.lower())
    
    return quality_score >= 2


def _enhance_query_with_keywords(query: str) -> str:
    """Add helpful keywords to improve search results."""
    keywords_to_add = []
    
    # Add current year for recent information
    keywords_to_add.append("2025")
    
    # Add context keywords based on query content
    if any(word in query.lower() for word in ["how", "tutorial", "guide"]):
        keywords_to_add.append("tutorial")
    
    if any(word in query.lower() for word in ["error", "problem", "issue", "fix"]):
        keywords_to_add.append("solution")
    
    if any(word in query.lower() for word in ["api", "code", "programming"]):
        keywords_to_add.append("documentation")
    
    enhanced = f"{query} {' '.join(keywords_to_add)}"
    return enhanced.strip()


def _generate_alternative_queries(query: str) -> List[str]:
    """Generate alternative phrasings of the search query."""
    alternatives = []
    
    # Synonym substitutions
    synonyms = {
        "how to": ["tutorial", "guide for", "steps to"],
        "error": ["problem", "issue", "bug"],
        "fix": ["solve", "resolve", "repair"],
        "best": ["top", "recommended", "optimal"],
        "install": ["setup", "configure", "deploy"],
        "create": ["make", "build", "generate"],
        "delete": ["remove", "destroy", "eliminate"]
    }
    
    query_lower = query.lower()
    for original, alts in synonyms.items():
        if original in query_lower:
            for alt in alts:
                alternatives.append(query_lower.replace(original, alt))
    
    # Add question formats
    if not query.endswith("?"):
        alternatives.append(f"What is {query}?")
        alternatives.append(f"How does {query} work?")
    
    # Add specific vs general versions
    if len(query.split()) > 3:
        # Make more specific
        alternatives.append(f'"{query}"')  # Exact phrase search
    else:
        # Make more general
        key_terms = query.split()[:2]  # Take first 2 words
        alternatives.append(" ".join(key_terms))
    
    return alternatives[:5]  # Return top 5 alternatives


def _extract_key_components(query: str) -> List[str]:
    """Extract key components from a complex query."""
    # Remove common stop words
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "how", "what", "when", "where", "why"}
    
    words = query.lower().split()
    key_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    components = []
    
    # Single key terms
    components.extend(key_words[:3])
    
    # Pairs of key terms
    for i in range(len(key_words) - 1):
        components.append(f"{key_words[i]} {key_words[i+1]}")
    
    return components[:4]


def _extract_key_terms(query: str) -> List[str]:
    """Extract the most important terms from a query for targeted search."""
    # Remove common words and extract meaningful terms
    words = re.findall(r'\b\w{3,}\b', query.lower())
    
    # Filter out very common words
    common_words = {"the", "and", "for", "are", "but", "not", "you", "all", "can", "her", "was", "one", "our", "had", "have", "what", "were", "said", "each", "which", "their", "time", "will", "about", "would", "there", "could", "other", "after", "first", "well", "many", "some", "these", "may", "then", "them", "more", "very", "what", "know", "just", "into", "over", "think", "also", "your", "work", "life", "only", "can", "still", "should", "being", "now", "made", "before", "here", "through", "when", "where", "much", "take", "than", "only", "little", "state", "good", "get", "own", "say", "she", "way", "use", "man", "new", "now", "old", "see", "him", "two", "how", "its", "who", "oil", "sit", "set"}
    
    key_terms = [word for word in words if word not in common_words]
    
    return key_terms[:5]


def _make_query_broader(query: str) -> str:
    """Make a query broader to catch more general information."""
    key_terms = _extract_key_terms(query)
    
    if len(key_terms) >= 2:
        # Use just the first two most important terms
        return " ".join(key_terms[:2])
    elif len(key_terms) == 1:
        # Add general context words
        return f"{key_terms[0]} overview guide"
    else:
        # Fallback to original query
        return query


# Export the enhanced search function
enhanced_search_tools = [
    intelligent_search
]