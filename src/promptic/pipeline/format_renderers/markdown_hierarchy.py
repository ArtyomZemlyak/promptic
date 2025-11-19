from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class Section:
    level: int
    title: str
    content: str = ""
    children: List["Section"] = field(default_factory=list)


@dataclass
class ConditionalSection:
    condition: str
    content: str
    start_index: int
    end_index: int


@dataclass
class MarkdownHierarchy:
    sections: List[Section] = field(default_factory=list)
    conditionals: List[ConditionalSection] = field(default_factory=list)


class MarkdownHierarchyParser:
    """
    Lightweight parser that extracts heading-based hierarchy and conditional markers.

    # AICODE-NOTE: Parsing happens once per render so downstream renderers can
    #              make deterministic decisions about which sections should be
    #              included without duplicating regex logic in multiple places.
    """

    HEADING_PATTERN = re.compile(r"^(?P<prefix>#{1,6})\s+(?P<title>.+)$")
    CONDITIONAL_PATTERN = re.compile(
        r"<!--\s*if:(?P<condition>[A-Za-z0-9_.\-]+)\s*-->(?P<body>.*?)<!--\s*endif\s*-->",
        flags=re.DOTALL | re.IGNORECASE,
    )

    def parse(self, content: str) -> MarkdownHierarchy:
        sections = self._build_sections(content)
        conditionals = self.extract_conditionals(content)
        return MarkdownHierarchy(sections=sections, conditionals=conditionals)

    def extract_conditionals(self, content: str) -> List[ConditionalSection]:
        matches: List[ConditionalSection] = []
        for match in self.CONDITIONAL_PATTERN.finditer(content):
            matches.append(
                ConditionalSection(
                    condition=match.group("condition").strip(),
                    content=match.group("body"),
                    start_index=match.start(),
                    end_index=match.end(),
                )
            )
        return matches

    def _build_sections(self, content: str) -> List[Section]:
        sections: List[Section] = []
        stack: List[Section] = []

        for line in content.splitlines():
            heading = self.HEADING_PATTERN.match(line.strip())
            if heading:
                level = len(heading.group("prefix"))
                title = heading.group("title").strip()
                section = Section(level=level, title=title)
                while stack and stack[-1].level >= level:
                    stack.pop()
                if stack:
                    stack[-1].children.append(section)
                else:
                    sections.append(section)
                stack.append(section)
            elif stack:
                stack[-1].content += line + "\n"
        return sections


__all__ = [
    "ConditionalSection",
    "MarkdownHierarchy",
    "MarkdownHierarchyParser",
    "Section",
]
