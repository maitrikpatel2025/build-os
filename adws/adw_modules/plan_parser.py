"""Product plan parser for Build OS.

Parses a Design OS product-plan/ folder and extracts structured data:
milestones, sections, design tokens, entities, and shell assets.
"""

import os
import re
from typing import List, Optional

from .data_types import (
    DesignSystem,
    MilestoneInstruction,
    ProductOverview,
    ProductPlan,
    SectionAssets,
    SectionComponent,
    ShellAssets,
)
from .utils import get_project_root


def parse_product_plan(plan_path: Optional[str] = None) -> ProductPlan:
    """Parse a complete product-plan/ directory into a structured ProductPlan.

    Args:
        plan_path: Path to the product-plan/ directory. Defaults to project_root/product-plan/

    Returns:
        ProductPlan with all parsed data
    """
    if plan_path is None:
        plan_path = os.path.join(get_project_root(), "product-plan")

    if not os.path.isabs(plan_path):
        plan_path = os.path.join(get_project_root(), plan_path)

    if not os.path.exists(plan_path):
        raise FileNotFoundError(f"Product plan not found at: {plan_path}")

    overview = parse_product_overview(plan_path)
    milestones = parse_milestones(plan_path)
    design_system = parse_design_system(plan_path)
    sections = parse_sections(plan_path)
    shell = parse_shell(plan_path)

    return ProductPlan(
        product_overview=overview,
        milestones=milestones,
        design_system=design_system,
        sections=sections,
        shell=shell,
    )


def parse_product_overview(plan_path: str) -> ProductOverview:
    """Parse product-overview.md to extract product metadata."""
    overview_path = os.path.join(plan_path, "product-overview.md")

    if not os.path.exists(overview_path):
        return ProductOverview(product_name="Unknown Product")

    with open(overview_path, "r") as f:
        content = f.read()

    # Extract product name from first H1
    name_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    product_name = name_match.group(1).strip() if name_match else "Unknown Product"

    # Extract description from first paragraph after the title
    desc_match = re.search(r"^#\s+.+\n\n(.+?)(?:\n\n|\n#)", content, re.MULTILINE | re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else None

    # Extract sections from a sections list (look for numbered or bulleted items under Sections heading)
    sections = []
    sections_match = re.search(
        r"##\s+(?:Sections|Pages|Views|Features)\s*\n((?:[\s\S]*?))\n(?:##|\Z)",
        content,
        re.MULTILINE,
    )
    if sections_match:
        section_text = sections_match.group(1)
        # Match bulleted or numbered list items
        for item in re.finditer(r"[-*\d.]+\s+\*?\*?([^*\n]+)", section_text):
            section_name = item.group(1).strip().rstrip("*")
            sections.append(section_name)

    # Extract entities from data shapes or entity mentions
    entities = []
    entities_match = re.search(
        r"##\s+(?:Entities|Data\s+Shapes?|Models?)\s*\n((?:[\s\S]*?))\n(?:##|\Z)",
        content,
        re.MULTILINE,
    )
    if entities_match:
        entity_text = entities_match.group(1)
        for item in re.finditer(r"[-*\d.]+\s+\*?\*?([^*\n]+)", entity_text):
            entity_name = item.group(1).strip().rstrip("*")
            entities.append(entity_name)

    return ProductOverview(
        product_name=product_name,
        description=description,
        sections=sections,
        entities=entities,
    )


def parse_milestones(plan_path: str) -> List[MilestoneInstruction]:
    """Parse instructions/incremental/ to extract milestone definitions."""
    incremental_path = os.path.join(plan_path, "instructions", "incremental")

    if not os.path.exists(incremental_path):
        return []

    milestones = []
    for filename in sorted(os.listdir(incremental_path)):
        if not filename.endswith(".md"):
            continue

        # Parse filename: "01-shell.md" → id="01-shell", order=1
        match = re.match(r"(\d+)-(.+)\.md$", filename)
        if not match:
            continue

        order = int(match.group(1))
        slug = match.group(2)
        milestone_id = f"{match.group(1)}-{slug}"

        # Determine section_id (shell has no section_id)
        section_id = None if slug == "shell" else slug

        # Extract name from file content or filename
        file_path = os.path.join(incremental_path, filename)
        name = slug.replace("-", " ").title()

        try:
            with open(file_path, "r") as f:
                first_line = f.readline().strip()
            # If first line is an H1 heading, use it as the name
            h1_match = re.match(r"^#\s+(.+)$", first_line)
            if h1_match:
                name = h1_match.group(1).strip()
        except Exception:
            pass

        milestones.append(
            MilestoneInstruction(
                id=milestone_id,
                name=name,
                section_id=section_id,
                instruction_path=file_path,
                order=order,
            )
        )

    return milestones


def parse_design_system(plan_path: str) -> DesignSystem:
    """Parse design-system/ directory for design tokens."""
    ds_path = os.path.join(plan_path, "design-system")

    if not os.path.exists(ds_path):
        return DesignSystem()

    design_system = DesignSystem()

    # Parse tokens.css
    tokens_css_path = os.path.join(ds_path, "tokens.css")
    if os.path.exists(tokens_css_path):
        with open(tokens_css_path, "r") as f:
            design_system.tokens_css = f.read()

    # Parse tailwind-colors.md for color palette
    colors_path = os.path.join(ds_path, "tailwind-colors.md")
    if os.path.exists(colors_path):
        with open(colors_path, "r") as f:
            colors_content = f.read()

        # Extract primary/secondary/neutral colors
        primary_match = re.search(r"primary[:\s]+(\w+)", colors_content, re.IGNORECASE)
        if primary_match:
            design_system.primary = primary_match.group(1).lower()

        secondary_match = re.search(r"secondary[:\s]+(\w+)", colors_content, re.IGNORECASE)
        if secondary_match:
            design_system.secondary = secondary_match.group(1).lower()

        neutral_match = re.search(r"neutral[:\s]+(\w+)", colors_content, re.IGNORECASE)
        if neutral_match:
            design_system.neutral = neutral_match.group(1).lower()

    # Parse fonts.md
    fonts_path = os.path.join(ds_path, "fonts.md")
    if os.path.exists(fonts_path):
        with open(fonts_path, "r") as f:
            fonts_content = f.read()

        fonts = {}
        heading_match = re.search(r"heading[:\s]+[\"']?([^\"'\n,]+)", fonts_content, re.IGNORECASE)
        if heading_match:
            fonts["heading"] = heading_match.group(1).strip()

        body_match = re.search(r"body[:\s]+[\"']?([^\"'\n,]+)", fonts_content, re.IGNORECASE)
        if body_match:
            fonts["body"] = body_match.group(1).strip()

        mono_match = re.search(r"mono(?:space)?[:\s]+[\"']?([^\"'\n,]+)", fonts_content, re.IGNORECASE)
        if mono_match:
            fonts["mono"] = mono_match.group(1).strip()

        if fonts:
            design_system.fonts = fonts

    return design_system


def parse_sections(plan_path: str) -> List[SectionAssets]:
    """Parse sections/ directory to catalog all section assets."""
    sections_path = os.path.join(plan_path, "sections")

    if not os.path.exists(sections_path):
        return []

    sections = []
    for section_id in sorted(os.listdir(sections_path)):
        section_dir = os.path.join(sections_path, section_id)
        if not os.path.isdir(section_dir):
            continue

        assets = SectionAssets(section_id=section_id)

        # Check for standard files
        readme = os.path.join(section_dir, "README.md")
        if os.path.exists(readme):
            assets.readme_path = readme

        types_file = os.path.join(section_dir, "types.ts")
        if os.path.exists(types_file):
            assets.types_path = types_file

        sample_data = os.path.join(section_dir, "sample-data.json")
        if os.path.exists(sample_data):
            assets.sample_data_path = sample_data

        screenshot = os.path.join(section_dir, "screenshot.png")
        if os.path.exists(screenshot):
            assets.screenshot_path = screenshot

        tests_file = os.path.join(section_dir, "tests.md")
        if os.path.exists(tests_file):
            assets.tests_path = tests_file

        # Catalog components
        components_dir = os.path.join(section_dir, "components")
        if os.path.exists(components_dir):
            for comp_file in sorted(os.listdir(components_dir)):
                if comp_file.endswith((".tsx", ".ts", ".jsx", ".js")) and comp_file != "index.ts":
                    assets.components.append(
                        SectionComponent(
                            name=comp_file,
                            path=os.path.join(components_dir, comp_file),
                        )
                    )

        sections.append(assets)

    return sections


def parse_shell(plan_path: str) -> ShellAssets:
    """Parse shell/ directory for shell assets."""
    shell_path = os.path.join(plan_path, "shell")

    if not os.path.exists(shell_path):
        return ShellAssets()

    assets = ShellAssets()

    readme = os.path.join(shell_path, "README.md")
    if os.path.exists(readme):
        assets.readme_path = readme

    components_dir = os.path.join(shell_path, "components")
    if os.path.exists(components_dir):
        for comp_file in sorted(os.listdir(components_dir)):
            if comp_file.endswith((".tsx", ".ts", ".jsx", ".js")) and comp_file != "index.ts":
                assets.components.append(
                    SectionComponent(
                        name=comp_file,
                        path=os.path.join(components_dir, comp_file),
                    )
                )

    return assets


def parse_entities_from_data_shapes(plan_path: str) -> List[str]:
    """Parse data-shapes/overview.ts to extract entity names."""
    overview_path = os.path.join(plan_path, "data-shapes", "overview.ts")

    if not os.path.exists(overview_path):
        return []

    with open(overview_path, "r") as f:
        content = f.read()

    # Extract interface/type names as entities
    entities = []
    for match in re.finditer(r"(?:export\s+)?(?:interface|type)\s+(\w+)", content):
        name = match.group(1)
        # Filter out utility types
        if not name.startswith("_") and name[0].isupper():
            entities.append(name)

    return entities
