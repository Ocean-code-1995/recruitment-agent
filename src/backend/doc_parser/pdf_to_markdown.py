"""
PDF to Markdown converter using GPT-4 Vision.

---------------------------------------------------------------------------
------------------------------ How to Use It ------------------------------
---------------------------------------------------------------------------
Process a single file:
>>> python pdf_to_markdown.py data_cv/max_mustermann_cv.pdf

Process a folder:
>>> python pdf_to_markdown.py data_cv/


Customize model or rendering:
>>> python pdf_to_markdown.py data_cv/ --model gpt-4.1 --target-width 1800 --batch-size 3


Disable column splitting:
>>> python pdf_to_markdown.py my_resume.pdf --no-halves


Set a custom output folder:
>>> python pdf_to_markdown.py data_cv/ --output processed/


🔧 Summary of Configurable Options
| Option                | Description                     | Default            |
| --------------------- | ------------------------------- | ------------------ |
| `path`                | PDF file or folder path         | required           |
| `--output`            | Output directory                | `results/`         |
| `--model`             | OpenAI model                    | `gpt-4.1-mini`     |
| `--target-width`      | Render width per page           | `2000`             |
| `--batch-size`        | Pages per API request           | `2`                |
| `--max-output-tokens` | Max tokens returned             | `8192`             |
| `--no-halves`         | Disable left/right column crops | Enabled by default |
"""

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

from .utils import (
    render_pdf_to_images,
    pil_to_png_data_uri,
    split_halves,
    parse_sections_from_json_text,
    normalize_sections,
    merge_duplicate_titles,
    build_contact_section_from_filename,
    process_section,
    apply_postprocessing,
)


def pdf_to_markdown(
    input_path: Path,
    output_path: Path,
    model: str = "gpt-4.1-mini",
    target_width: int = 2000,
    batch_size: int = 2,
    max_output_tokens: int = 8192,
    add_halves: bool = True,
) -> None:
    """
    Process a single PDF or all PDFs in a directory and export Markdown sections.
    
    1. Render PDF pages to images.
    2. Send images in batches to GPT-4 Vision for section parsing.
    3. Normalize and post-process the returned sections.
    4. Save the final sections as a Markdown text file.
    5. Repeat for all PDFs in the input path.
    6. Output files are saved in the specified output directory.

    Args:
        input_path: Path to a single PDF file or a directory of PDFs.
        output_path: Directory to save the output Markdown files.
        model: OpenAI model to use for processing.
        target_width: Target width for rendering PDF pages.
        batch_size: Number of pages to send per API request.
        max_output_tokens: Maximum tokens in model output.
        add_halves: Whether to add left/right column crops.
    """
    load_dotenv()

    def log_step(message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    log_step("Vision-based PDF → Markdown extraction started...")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your environment or .env file.")

    # --- Determine which PDFs to process ---
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        pdf_files = [input_path]
    elif input_path.is_dir():
        pdf_files = sorted(input_path.glob("*.pdf"))
    else:
        raise ValueError(f"Invalid input path: {input_path}")

    if not pdf_files:
        log_step(f"No PDF files found at {input_path}")
        return

    output_path.mkdir(parents=True, exist_ok=True)
    log_step(f"Found {len(pdf_files)} PDF file(s) in {input_path}.")
    log_step(f"Using model={model}, batch_size={batch_size}, target_width={target_width}px.")

    client = OpenAI()

    # -------------------------- Inner helper --------------------------
    def call_batch(imgs: List[Image.Image]) -> List[Dict[str, str]]:
        """Process a batch of page images → STRICT JSON sections."""
        image_contents = []
        for img in imgs:
            data_uri = pil_to_png_data_uri(img)
            image_contents.append({"type": "input_image", "image_url": data_uri})

            if add_halves:
                for half in split_halves(img):
                    image_contents.append(
                        {"type": "input_image", "image_url": pil_to_png_data_uri(half)}
                    )

        system = "You are a precise document structure parser. Output ONLY valid JSON."
        user = (
            "From these page images, return a STRICT JSON array where each item has 'title' and 'body'. "
            "Group human-meaningful sections, merge multi-line headings (two-column layouts), preserve reading order. "
            "Do NOT summarize or omit content. Include headers/footers if they contain contact data. "
            "Preserve bullet/numbered lists and render tables as Markdown where possible. "
            "Use proper UTF-8 German diacritics (ä, ö, ü, ß). "
            "Include small sidebar/column blocks and deduplicate content across full pages and crops."
        )

        response = client.responses.create(
            model=model,
            temperature=0,
            max_output_tokens=max_output_tokens,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": system}]},
                {"role": "user", "content": [{"type": "input_text", "text": user}] + image_contents},
            ],
        )

        text = getattr(response, "output_text", "") or ""
        return parse_sections_from_json_text(text)

    # -------------------------- Main processing --------------------------
    total_files = len(pdf_files)
    for index, pdf_file in enumerate(pdf_files, start=1):
        log_step(f"[{index}/{total_files}] Processing {pdf_file.name}...")
        pages = render_pdf_to_images(pdf_file, target_width=target_width)

        if not pages:
            raise RuntimeError(f"Failed to render any PDF pages for {pdf_file}.")

        log_step(f"Rendered {len(pages)} page(s).")

        all_sections: List[Dict[str, str]] = []
        for start in range(0, len(pages), batch_size):
            end = min(len(pages), start + batch_size)
            batch_num = (start // batch_size) + 1
            log_step(f"Batch {batch_num}: pages {start + 1}–{end}.")
            secs = call_batch(pages[start:end])
            if secs:
                all_sections.extend(secs)
                log_step(f"Batch {batch_num} returned {len(secs)} section(s).")
            else:
                log_step(f"Batch {batch_num} returned no sections.")

        if not all_sections:
            raise RuntimeError(f"No sections parsed from vision model output for {pdf_file}.")

        log_step(f"Received {len(all_sections)} raw section(s).")
        normalized = normalize_sections(all_sections)
        merged = merge_duplicate_titles(normalized)
        final_sections = apply_postprocessing(merged)
        contact_section = process_section(build_contact_section_from_filename(pdf_file))
        final_sections.insert(0, contact_section)

        out_txt = output_path / f"{pdf_file.stem}.txt"
        log_step(f"Writing output to {out_txt}...")

        lines: List[str] = []
        for sec in final_sections:
            title = (sec.get("title") or "").strip()
            body = (sec.get("body") or "").strip()
            if title:
                lines.append(f"## {title}")
            if body:
                lines.append(body)
            lines.append("")

        while lines and lines[-1] == "":
            lines.pop()

        out_txt.write_text("\n".join(lines), encoding="utf-8")
        log_step(f"✅ Completed processing for {pdf_file.name}.")

    log_step("🎉 All PDF files processed successfully.")
    print(f"\nResults saved in: {output_path.resolve()}")


# ----------------------------- CLI entrypoint -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert PDFs to structured Markdown using GPT-4 Vision."
    )
    parser.add_argument(
        "path",
        help="Path to a single PDF file or a directory containing PDF files.",
    )
    parser.add_argument(
        "-o", "--output",
        default="results",
        help="Output directory for the Markdown files (default: results/)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        help="OpenAI model to use (default: gpt-4.1-mini)",
    )
    parser.add_argument(
        "--target-width",
        type=int,
        default=int(os.getenv("VISION_TARGET_WIDTH", "2000")),
        help="Target width for rendering PDF pages (default: 2000 px)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.getenv("VISION_BATCH_PAGES", "2")),
        help="Number of pages to send to the model per request (default: 2)",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=int(os.getenv("MAX_OUTPUT_TOKENS", "8192")),
        help="Maximum tokens in model output (default: 8192)",
    )
    parser.add_argument(
        "--no-halves",
        action="store_true",
        help="Disable left/right column splitting (default: enabled)",
    )

    args = parser.parse_args()

    pdf_to_markdown(
        input_path=Path(args.path),
        output_path=Path(args.output),
        model=args.model,
        target_width=args.target_width,
        batch_size=args.batch_size,
        max_output_tokens=args.max_output_tokens,
        add_halves=not args.no_halves,
    )
