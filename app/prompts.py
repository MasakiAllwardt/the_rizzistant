"""Claude API prompt templates"""
from typing import List, Dict, Optional


def build_date_analysis_prompt(
    current_text: str,
    accumulated_transcript: str,
    previous_warnings: List[Dict] = None
) -> str:
    """Build prompt for analyzing date conversation and determining if intervention is needed"""
    previous_warnings_text = ""
    if previous_warnings and len(previous_warnings) > 0:
        previous_warnings_text = "\n\nPrevious warnings already sent (DO NOT repeat similar warnings):\n"
        for warning in previous_warnings:
            previous_warnings_text += f"- {warning['reason']}: {warning['message']}\n"

    return f"""You are monitoring a date conversation. Analyze the following transcript and determine if the person is discussing something really wrong that needs urgent changing. Keep track of the flow of the conversation and only give suggestions based on what the male is saying.

SPECIAL RULE: If they are talking about computer science topics, this is considered a really wrong topic that urgently needs to be changed.

IMPORTANT: You have already sent the warnings listed below. DO NOT send similar or duplicate warnings. Only notify if there is a NEW issue that hasn't been warned about yet.{previous_warnings_text}

Current segment: {current_text}

Full accumulated date transcript so far:
{accumulated_transcript}

Respond ONLY with valid JSON, no other text. Use this exact format:
{{
    "should_notify": true,
    "reason": "brief reason if notification needed",
    "message": "the warning message to send to user if notification needed"
}}

CRITICAL: The warning message must be a SINGLE CASUAL SENTENCE that is funny and nonchalant. Be roasting and playful like a friend calling them out. Examples:
- "yo shut up about one piece bro"
- "bro really talking about python on a date rn"
- "dawg nobody wants to hear about binary search trees"
- "my guy you gotta chill with the anime talk"

Be strict about computer science topics - any mention of programming, algorithms, data structures, etc. should trigger a notification. However, do NOT send duplicate warnings for issues you've already warned about."""


def build_conversation_tip_prompt(accumulated_transcript: str) -> str:
    """Build prompt for generating a helpful conversation tip when user seems stuck"""
    return f"""You are a real-time dating coach. The person on a date just said something like "yeah okay so" which suggests they might be stuck or transitioning awkwardly in the conversation.

Based on the conversation so far, provide ONE short, actionable tip (very short sentences) to help them continue the conversation naturally and engagingly.

Make the tip specific to their current conversation context if possible. Focus on:
- Asking an interesting follow-up question
- Sharing a related personal story
- Making a playful observation
- Changing the topic smoothly
- For example, if the girl mentioned an interest earlier in the date say "ask her to expand more on figure skating"
Keep it casual and conversational, not robotic. Don't mention that they said "yeah okay so".

Date transcript so far:
{accumulated_transcript}

Respond with ONLY the tip, no extra formatting or preamble."""


def build_date_summary_prompt(
    accumulated_transcript: str,
    previous_summary: Optional[str] = None
) -> str:
    """Build prompt for summarizing the date and providing tips for improvement"""
    previous_context = ""
    comparison_note = ""
    improvements_section = ""
    persistent_issues_section = ""

    if previous_summary:
        previous_context = f"""

    PREVIOUS DATE SUMMARY:
    {previous_summary}

    IMPORTANT: Compare this date to the previous one. Highlight specific improvements made,
    areas where the user applied previous advice, and new areas that need attention.
    Be concrete about what changed (better or worse) since the last date."""
        comparison_note = " Explicitly state how this date compares to the previous one (better/worse/similar and why)."
        improvements_section = "\n    - **Improvements from Last Date**: [List specific improvements observed]"
        persistent_issues_section = "\n    - **Persistent Issues**: [Note any problems that carried over from the previous date]"

    return f"""You are an elite dating coach and conversational analyst. Provide a comprehensive, structured report on this date conversation. This is a REPORT ONLY - do not ask any follow-up questions or include prompts for the user to respond.{previous_context}

    Your analysis must follow this EXACT structure:

    # DATE PERFORMANCE REPORT

    ## OVERALL ASSESSMENT
    Provide a 2-3 sentence executive summary of the date's success. Include: chemistry level (strong/moderate/weak), conversational balance (balanced/one-sided), and overall vibe (engaged/surface-level/disconnected).{comparison_note}

    ## PERFORMANCE SCORES

    ### Overall Score: [X.X/10]

    ### Category Breakdown:
    - **Emotional Awareness (20%)**: [X/10] - [One sentence assessment]
    - **Conversational Flow (20%)**: [X/10] - [One sentence assessment]
    - **Authenticity & Presence (15%)**: [X/10] - [One sentence assessment]
    - **Curiosity & Engagement (15%)**: [X/10] - [One sentence assessment]
    - **Confidence (10%)**: [X/10] - [One sentence assessment]
    - **Listening & Responsiveness (10%)**: [X/10] - [One sentence assessment]
    - **Humor & Playfulness (5%)**: [X/10] - [One sentence assessment]
    - **Flirtation & Chemistry (5%)**: [X/10] - [One sentence assessment]

    ## KEY HIGHLIGHTS
    List 3-4 specific moments where you excelled. Include brief quotes from the transcript.
    - [Strength 1]: [Quote or paraphrase]
    - [Strength 2]: [Quote or paraphrase]
    - [Strength 3]: [Quote or paraphrase]{improvements_section}

    ## CRITICAL WEAKNESSES
    List 2-4 specific issues that hurt the connection. Be direct and specific.
    - [Weakness 1]: [Specific example]
    - [Weakness 2]: [Specific example]{persistent_issues_section}

    ## EMOTIONAL DYNAMICS
    Analyze the underlying emotional flow:
    - **Interest Level**: [Their apparent interest - high/moderate/low with evidence]
    - **Power Dynamic**: [Who led the conversation, energy balance]
    - **Tension Points**: [Moments of awkwardness, disconnection, or friction]
    - **Connection Moments**: [Moments of genuine rapport or chemistry]

    ## ACTION PLAN FOR NEXT DATE
    Provide 3 concrete, specific behavioral strategies. NO generic advice.
    1. **[Strategy 1]**: [Specific action with example]
    2. **[Strategy 2]**: [Specific action with example]
    3. **[Strategy 3]**: [Specific action with example]

    CRITICAL RULES:
    - This is a REPORT. Do not include questions for the user.
    - Do not ask "How did you feel about..." or any similar prompts
    - Be direct, honest, and specific with examples
    - Use actual quotes from the transcript when highlighting moments
    - Keep each section concise but informative
    - Focus on actionable insights, not platitudes

    Date transcript:
    {accumulated_transcript}"""
