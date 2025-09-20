# LLM Instruction Format Specification

## 1. Overview

This document defines the final output format of the AI Agent Instruction Prompt. The format is a result of a deterministic, rule-based transformation of GitHub PR data into a structured, machine-readable, and AI-friendly prompt.

The key characteristic of this format is that it is generated **without the use of any LLM**. It is a direct, mechanical structuring of raw data fetched via the GitHub CLI, designed to be consumed by an LLM agent.

## 2. Design Philosophy

- **LLM-Free Generation**: The format is a raw representation of fetched data, structured for AI consumption. There is no AI-driven summarization or analysis in the generation process itself.
- **Clarity through Structure**: Adopts Claude 4's best practice of using XML-style tags to give structure to the raw text data from GitHub, making it easier for the receiving AI to parse and understand the role of each piece of information.
- **Single Source of Truth**: All content within the dynamic sections of the prompt is directly traceable to the output of the GitHub CLI, ensuring data integrity.

## 3. Format Specification

The output is a single Markdown file with embedded XML-style tags. It follows the structure of the `expected_pr_*.md` golden files.

```markdown
# CodeRabbit Review Analysis - AI Agent Prompt

<role>
...
</role>

<core_principles>
...
</core_principles>

<analysis_methodology>
...
</analysis_methodology>

## Pull Request Context
...

## CodeRabbit Review Summary
...

---

# Analysis Task

...

<output_requirements>
...
</output_requirements>

# CodeRabbit Comments for Analysis

<review_comments>
  <review_comment type="{string}" file="{string}" lines="{string}">
    <issue>
      {string: comment title}
    </issue>
    <instructions>
      {string: comment body/instructions}
    </instructions>
    <proposed_diff><![CDATA[
      {string: code diff}
]]></proposed_diff>
  </review_comment>

  <!-- ... more review_comment blocks ... -->

</review_comments>

---

# Analysis Instructions

<thinking_framework>
...
</thinking_framework>

**Begin your analysis with the first comment and proceed systematically through each category.**
```

### 3.1. Header Sections (Static)

- **`<role>`**, **`<core_principles>`**, **`<analysis_methodology>`**: These are static text blocks that define the persona and high-level instructions for the AI agent. They are the same in every generated prompt.

### 3.2. Context Sections (Dynamic)

- **`## Pull Request Context`**: Populated with metadata from the GitHub PR (URL, title, author, etc.).
- **`## CodeRabbit Review Summary`**: Contains mechanically counted statistics of the comments, categorized by type.

### 3.3. Task Sections (Static)

- **`# Analysis Task`**, **`<output_requirements>`**: Static instructions that tell the AI agent what to do with the comments and how to format its own output.

### 3.4. Core Data Section: `<review_comments>` (Dynamic)

This is the main data payload.

- **`<review_comments>`**: The root container for all review comments.
- **`<review_comment>`**: Represents a single, discrete piece of feedback from CodeRabbit.
    - **`type` attribute**: The comment category (`Actionable`, `Nitpick`, `OutsideDiff`). Determined by parsing headers in the CodeRabbit review summary.
    - **`file` attribute**: The relevant file path.
    - **`lines` attribute**: The relevant line numbers.
- **`<issue>`**: The title of the comment, extracted directly from the review.
- **`<instructions>`**: The full body text of the comment. This provides the core instruction from CodeRabbit.
- **`<proposed_diff>`**: (Optional) The suggested code change, extracted from a `diff` code block in the comment. It is wrapped in `CDATA` to handle special characters correctly.

### 3.5. Footer Section (Static)

- **`# Analysis Instructions`**: A static concluding section, often containing a `<thinking_framework>` to guide the AI's internal process.

## 4. Conclusion

This format strictly adheres to the principle of separating data collection/structuring from data analysis. The `coderabbit-fetcher` tool acts as a deterministic data preprocessor, creating a clean, structured, and predictable input. The subsequent analysis and interpretation are entirely the responsibility of the AI agent that consumes this prompt.