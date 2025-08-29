from pathlib import Path


def main() -> None:
    """
    Reads key project documents and combines them into a single context pack
    file.
    """
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "context"
    output_file = output_dir / "_pack.md"

    # Ensure the output directory exists
    output_dir.mkdir(exist_ok=True)

    source_files = [
        "docs/ARCHITECTURE.md",
        "docs/TASKS.md",
        "docs/dev_log.md",
        "PROMPTS.md",
    ]

    with open(output_file, "w", encoding="utf-8") as outfile:
        for file_path_str in source_files:
            file_path = project_root / file_path_str
            if file_path.exists():
                header = f"# === {file_path_str} ===\n\n"
                content = file_path.read_text(encoding="utf-8")
                outfile.write(header)
                outfile.write(content)
                outfile.write("\n\n")
            else:
                # Silently skip missing files as per instructions
                pass

    print("✅ context/_pack.md 已生成")


if __name__ == "__main__":
    main()
