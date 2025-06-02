# twincli/tools/research_orchestrator.py
"""
Research orchestrator that coordinates multiple search strategies and sources.

Category: research
Created: 2025-06-01
"""

import re
import time
from typing import List, Dict, Optional, Tuple
from twincli.tools.enhanced_search import search_web
from twincli.tools.obsidian import search_obsidian
from twincli.tools.enhanced_search import intelligent_search


def comprehensive_research(topic: str, research_depth: str = "medium", time_limit_minutes: int = 5) -> str:
    """
    Conducts comprehensive research on a topic using multiple sources and strategies.
    
    Args:
        topic: The research topic or question
        research_depth: "quick" (1-2 searches), "medium" (3-5 searches), "deep" (5+ searches)
        time_limit_minutes: Maximum time to spend on research
        
    Returns:
        Comprehensive research report with findings from multiple sources
    """
    start_time = time.time()
    research_log = []
    findings = []
    sources_used = []
    
    # Determine search strategy based on depth
    max_searches = {"quick": 2, "medium": 5, "deep": 10}.get(research_depth, 5)
    
    research_log.append(f"🔬 **Starting Comprehensive Research**")
    research_log.append(f"Topic: {topic}")
    research_log.append(f"Depth: {research_depth} (max {max_searches} searches)")
    research_log.append(f"Time limit: {time_limit_minutes} minutes")
    research_log.append("")
    
    # Phase 1: Primary web search with intelligent strategies
    research_log.append("📡 **Phase 1: Intelligent Web Search**")
    try:
        web_results = intelligent_search(topic, max_attempts=3)
        findings.append(("Web Search", web_results))
        sources_used.append("Web (Multi-strategy)")
        research_log.append("✓ Completed intelligent web search")
    except Exception as e:
        research_log.append(f"✗ Web search failed: {e}")
    
    # Phase 2: Personal knowledge base search
    if time.time() - start_time < time_limit_minutes * 60 * 0.4:  # Use 40% of time for this phase
        research_log.append("\n📚 **Phase 2: Personal Knowledge Base**")
        try:
            obsidian_results = search_obsidian(topic)
            if "Found" in obsidian_results:
                findings.append(("Personal Notes", obsidian_results))
                sources_used.append("Obsidian Vault")
                research_log.append("✓ Found relevant personal notes")
            else:
                research_log.append("ℹ No relevant personal notes found")
        except Exception as e:
            research_log.append(f"✗ Personal knowledge search failed: {e}")
    
    # Phase 3: Targeted follow-up searches based on initial findings
    if len(findings) > 0 and time.time() - start_time < time_limit_minutes * 60 * 0.7:
        research_log.append("\n🎯 **Phase 3: Targeted Follow-up**")
        follow_up_queries = _generate_follow_up_queries(topic, findings)
        
        for i, follow_up in enumerate(follow_up_queries[:2]):  # Limit to 2 follow-ups
            if time.time() - start_time >= time_limit_minutes * 60 * 0.9:
                research_log.append("⏰ Time limit approaching, stopping follow-up searches")
                break
                
            try:
                follow_up_result = search_web(follow_up)
                if _is_substantial_result(follow_up_result):
                    findings.append((f"Follow-up: {follow_up}", follow_up_result))
                    sources_used.append(f"Web Follow-up {i+1}")
                    research_log.append(f"✓ Follow-up search successful: {follow_up}")
                else:
                    research_log.append(f"ℹ Follow-up search limited results: {follow_up}")
            except Exception as e:
                research_log.append(f"✗ Follow-up search failed: {follow_up} - {e}")
    
    # Phase 4: Gap analysis and additional targeted searches
    if research_depth == "deep" and time.time() - start_time < time_limit_minutes * 60 * 0.85:
        research_log.append("\n🔍 **Phase 4: Gap Analysis & Deep Search**")
        gaps = _identify_research_gaps(topic, findings)
        
        for gap in gaps[:2]:  # Address top 2 gaps
            if time.time() - start_time >= time_limit_minutes * 60 * 0.95:
                break
                
            try:
                gap_result = search_web(gap)
                if _is_substantial_result(gap_result):
                    findings.append((f"Gap Analysis: {gap}", gap_result))
                    sources_used.append("Deep Search")
                    research_log.append(f"✓ Gap search successful: {gap}")
            except Exception as e:
                research_log.append(f"✗ Gap search failed: {gap} - {e}")
    
    # Compile comprehensive report
    elapsed_time = time.time() - start_time
    
    report = f"""🔬 **COMPREHENSIVE RESEARCH REPORT**

**Topic:** {topic}
**Research Depth:** {research_depth}
**Time Elapsed:** {elapsed_time:.1f} seconds
**Sources Consulted:** {', '.join(sources_used)}
**Total Findings:** {len(findings)}

---

## 📊 EXECUTIVE SUMMARY

{_generate_executive_summary(topic, findings)}

---

## 🔍 DETAILED FINDINGS

"""
    
    for i, (source, content) in enumerate(findings, 1):
        report += f"### {i}. {source}\n\n"
        # Truncate very long results but provide substance
        if len(content) > 1500:
            report += content[:1500] + "\n\n*[Result truncated for readability]*\n\n"
        else:
            report += content + "\n\n"
        report += "---\n\n"
    
    # Add research quality assessment
    report += f"""## 📈 RESEARCH QUALITY ASSESSMENT

**Coverage:** {_assess_coverage(topic, findings)}
**Source Diversity:** {len(set(sources_used))} different source types
**Depth Score:** {len(findings)}/10
**Confidence Level:** {_assess_confidence(findings)}

## 🎯 KEY INSIGHTS

{_extract_key_insights(topic, findings)}

## 📝 RESEARCH LOG

{chr(10).join(research_log)}

---

**Note:** This research was conducted using automated multi-source search strategies. Results should be verified for critical decisions.
"""
    
    return report


def _generate_follow_up_queries(topic: str, findings: List[Tuple[str, str]]) -> List[str]:
    """Generate intelligent follow-up queries based on initial findings."""
    follow_ups = []
    
    # Extract key terms mentioned in findings
    all_content = " ".join([content for _, content in findings])
    
    # Look for mentioned but unexplored topics
    potential_terms = re.findall(r'\b[A-Z][a-zA-Z]{3,}\b', all_content)
    unique_terms = list(set(potential_terms))[:5]
    
    # Generate specific follow-up queries
    follow_ups.extend([f"{topic} {term}" for term in unique_terms[:2]])
    
    # Add contextual follow-ups
    if "error" in topic.lower() or "problem" in topic.lower():
        follow_ups.append(f"{topic} solution tutorial")
        follow_ups.append(f"how to fix {topic}")
    
    if "best" in topic.lower() or "recommend" in topic.lower():
        follow_ups.append(f"{topic} comparison 2025")
        follow_ups.append(f"{topic} pros and cons")
    
    return follow_ups[:3]


def _identify_research_gaps(topic: str, findings: List[Tuple[str, str]]) -> List[str]:
    """Identify potential gaps in research coverage."""
    gaps = []
    
    # Common research angles that might be missing
    research_angles = [
        f"{topic} latest developments",
        f"{topic} alternatives",
        f"{topic} case studies",
        f"{topic} implementation guide",
        f"{topic} best practices",
        f"{topic} common mistakes",
        f"{topic} cost analysis",
        f"{topic} security considerations"
    ]
    
    # Check which angles haven't been covered
    all_content_lower = " ".join([content.lower() for _, content in findings])
    
    for angle in research_angles:
        key_words = angle.lower().split()[-2:]  # Last 2 words
        if not all(word in all_content_lower for word in key_words):
            gaps.append(angle)
    
    return gaps[:4]


def _is_substantial_result(result: str) -> bool:
    """Check if a search result is substantial and useful."""
    if not result or len(result) < 200:
        return False
    
    # Check for useful content indicators
    useful_indicators = ["http", "description", "explanation", "guide", "tutorial", "steps", "process", "method"]
    indicator_count = sum(1 for indicator in useful_indicators if indicator.lower() in result.lower())
    
    return indicator_count >= 2


def _generate_executive_summary(topic: str, findings: List[Tuple[str, str]]) -> str:
    """Generate an executive summary of research findings."""
    if not findings:
        return f"Research on '{topic}' yielded limited results. Consider refining the search terms or exploring alternative sources."
    
    summary_points = []
    
    # Analyze findings for key themes
    all_content = " ".join([content for _, content in findings])
    
    # Extract key insights
    if len(findings) >= 3:
        summary_points.append(f"✓ Comprehensive research conducted across {len(findings)} sources")
    elif len(findings) >= 1:
        summary_points.append(f"✓ Research conducted with {len(findings)} primary source(s)")
    
    # Look for solution indicators
    if any(word in all_content.lower() for word in ["solution", "fix", "resolve", "answer"]):
        summary_points.append("✓ Potential solutions and fixes identified")
    
    # Look for tutorial/guide content
    if any(word in all_content.lower() for word in ["tutorial", "guide", "steps", "how to"]):
        summary_points.append("✓ Instructional content and guides located")
    
    # Look for recent information
    if "2025" in all_content or "2024" in all_content:
        summary_points.append("✓ Recent and up-to-date information found")
    
    if not summary_points:
        summary_points.append("ℹ Basic information gathered, may require additional research")
    
    return "\n".join(summary_points)


def _assess_coverage(topic: str, findings: List[Tuple[str, str]]) -> str:
    """Assess how well the research covers the topic."""
    if len(findings) == 0:
        return "No coverage"
    elif len(findings) == 1:
        return "Minimal coverage"
    elif len(findings) <= 3:
        return "Basic coverage"
    elif len(findings) <= 5:
        return "Good coverage"
    else:
        return "Comprehensive coverage"


def _assess_confidence(findings: List[Tuple[str, str]]) -> str:
    """Assess confidence level in research results."""
    if not findings:
        return "Very Low"
    
    # Count quality indicators across all findings
    quality_score = 0
    for _, content in findings:
        if len(content) > 500:
            quality_score += 2
        elif len(content) > 200:
            quality_score += 1
        
        if "http" in content:
            quality_score += 1
        if any(word in content.lower() for word in ["documentation", "official", "guide"]):
            quality_score += 2
    
    if quality_score >= 8:
        return "High"
    elif quality_score >= 5:
        return "Medium"
    elif quality_score >= 2:
        return "Low"
    else:
        return "Very Low"


def _extract_key_insights(topic: str, findings: List[Tuple[str, str]]) -> str:
    """Extract key insights from research findings."""
    if not findings:
        return "No significant insights available from current research."
    
    insights = []
    
    # Look for common themes across findings
    all_content = " ".join([content for _, content in findings]).lower()
    
    # Extract frequently mentioned terms (simple approach)
    words = re.findall(r'\b\w{4,}\b', all_content)
    word_freq = {}
    for word in words:
        if word not in ["this", "that", "with", "from", "they", "were", "been", "have", "will"]:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get most frequent meaningful terms
    frequent_terms = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    if frequent_terms:
        key_terms = [term for term, count in frequent_terms if count >= 2]
        if key_terms:
            insights.append(f"• Frequently mentioned topics: {', '.join(key_terms[:3])}")
    
    # Add source diversity insight
    source_types = [source for source, _ in findings]
    insights.append(f"• Information gathered from: {', '.join(set(source_types))}")
    
    # Add coverage insight
    insights.append(f"• Research depth: {len(findings)} distinct information sources")
    
    return "\n".join(insights) if insights else "Additional analysis needed to extract meaningful insights."


# Export the research orchestrator
research_tools = [
    comprehensive_research
]