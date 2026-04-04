#!/usr/bin/env python3
"""
生成遷移狀態檔案 (snapshot_migration_status.json)
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add the script directory to path so we can import migration_tracker
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

from migration_tracker import MigrationStatusTracker  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Generate migration status snapshot.")
    parser.add_argument(
        "-s",
        "--snapshots",
        type=str,
        default="snapshots",
        help="Snapshots directory path (default: snapshots)",
    )
    args = parser.parse_args()

    snapshots_dir = Path(args.snapshots).resolve()
    css_snapshot = snapshots_dir / "snapshot_css_classes.json"
    templates_snapshot = snapshots_dir / "snapshot_templates.json"
    output_path = snapshots_dir / "snapshot_migration_status.json"

    if not css_snapshot.exists():
        print(f"Error: CSS snapshot not found at {css_snapshot}")
        print("Please run css_scanner.py first.")
        sys.exit(1)

    if not templates_snapshot.exists():
        print(f"Error: Templates snapshot not found at {templates_snapshot}")
        print("Please run standalone_snapshot.py first.")
        sys.exit(1)

    print("Initializing MigrationStatusTracker...")
    try:
        tracker = MigrationStatusTracker(css_snapshot, templates_snapshot)

        print("Detecting conflicts...")
        tracker.detect_conflicts()

        print("Initializing migration status...")
        tracker.initialize_migration_status()

        # Try to load existing status to preserve progress
        if output_path.exists():
            print("Loading existing migration status to preserve progress...")
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    existing_templates = existing_data.get("templates", {})
                    # Update tracker with existing status
                    for name, record in tracker.migration_status.items():
                        if name in existing_templates:
                            existing_record = existing_templates[name]
                            record["status"] = existing_record.get(
                                "status", "not_started"
                            )
                            record["notes"] = existing_record.get("notes", "")
                            record["started_at"] = existing_record.get("started_at")
                            record["completed_at"] = existing_record.get("completed_at")
            except Exception as e:
                print(f"Warning: Could not load existing status: {e}")

        print(f"Saving migration status to {output_path}...")

        # Adapt to standalone_migration_status.py expectations (matching 'templates' key)
        adapted_templates = {}
        for name, record in tracker.migration_status.items():
            adapted_templates[name] = {
                "template_name": record["template_name"],
                "status": record["status"],
                "complexity": record["complexity_score"],
                "dependencies": record["dependencies"],
                "dependency_depth": record["dependency_depth"],
                "conflicts": len(record["conflicts"]),
                "started_at": record["started_at"],
                "completed_at": record["completed_at"],
                "last_updated": record["last_updated"],
                "notes": record["notes"],
            }

        output_data = {
            "generated_at": datetime.now().isoformat(),
            "templates": adapted_templates,
            "statistics": tracker.get_statistics(),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print("Done!")

    except Exception as e:
        print(f"Error generating migration status: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
