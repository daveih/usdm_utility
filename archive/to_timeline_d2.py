import os
import argparse
import subprocess
from uuid import uuid4
from usdm4.api.scheduled_instance import (
    ScheduledActivityInstance,
    ScheduledDecisionInstance,
    ScheduledInstance,
)
from usdm4.api.wrapper import Wrapper
from usdm4.api.study_design import StudyDesign
from usdm4.api.schedule_timeline_exit import ScheduleTimelineExit
from usdm4 import USDM4
from usdm4.builder.builder import Builder
from simple_error_log.errors import Errors


class Timeline:
    def __init__(self, file_path: str, errors: Errors):
        self._errors = errors
        self._usdm = USDM4()
        self._file_path = file_path
        self._builder: Builder = self._usdm.builder(errors)

    def get_timelines(self):
        """Get all timelines from USDM data."""
        self._builder.seed(self._file_path)
        wrapper_dict: dict = self._builder._data_store.data
        wrapper_dict["study"]["id"] = uuid4()
        wrapper = Wrapper.model_validate(wrapper_dict)
        try:
            study_design = wrapper.study.versions[0].studyDesigns[0]
            return study_design.scheduleTimelines
        except Exception as e:
            self._errors.exception(f"Failed accessing timelines", e)
            return []

    def generate_timeline_d2(self, timeline):
        """Generate D2 syntax for a single timeline."""
        d2_lines = []
        d2_lines.append("# USDM Timeline Visualization")
        d2_lines.append(f"# Timeline: {timeline.label}")
        d2_lines.append(f"# Condition: {timeline.entryCondition}")
        d2_lines.append("direction: right")
        d2_lines.append("")

        try:
            timings = timeline.timings

            # First, collect all instances in sequence
            instances = []
            instance = self._get_cross_reference(timeline.entryId)
            while instance:
                instances.append(instance)
                instance = self._get_cross_reference(instance.get("defaultConditionId"))

            # Separate activity and decision instances
            activity_instances = [
                inst
                for inst in instances
                if inst["instanceType"] == ScheduledActivityInstance.__name__
            ]
            decision_instances = [
                inst
                for inst in instances
                if inst["instanceType"] != ScheduledActivityInstance.__name__
            ]

            # Timeline entry node (pill/capsule shape)
            d2_lines.append(f'{timeline.id}: "{timeline.label}" {{')
            d2_lines.append("  shape: oval")
            d2_lines.append("  width: 150")
            d2_lines.append("  height: 60")
            d2_lines.append("  style: {")
            d2_lines.append('    fill: "#90EE90"')
            d2_lines.append('    stroke: "#006400"')
            d2_lines.append("    stroke-width: 2")
            d2_lines.append("  }")
            d2_lines.append("}")
            d2_lines.append("")

            # Add all activity instances at root level
            for inst in activity_instances:
                d2_lines.append(f'{inst["id"]}: "ScheduledActivityInstance" {{')
                d2_lines.append("  shape: rectangle")
                d2_lines.append("  style: {")
                d2_lines.append('    fill: "#ADD8E6"')
                d2_lines.append('    stroke: "#4169E1"')
                d2_lines.append("  }")
                d2_lines.append("}")
                d2_lines.append("")

            # Connect timeline entry to first activity instance
            if activity_instances:
                d2_lines.append(
                    f"{timeline.id} -> {activity_instances[0]['id']}: first"
                )
                d2_lines.append("")

            # Add connections between activity instances
            for i in range(len(activity_instances) - 1):
                d2_lines.append(
                    f"{activity_instances[i]['id']} -> {activity_instances[i + 1]['id']}"
                )
                d2_lines.append("")

            # Add decision instances
            for inst in decision_instances:
                d2_lines.append(f'{inst["id"]}: "ScheduledDecisionInstance" {{')
                d2_lines.append("  shape: diamond")
                d2_lines.append("  style: {")
                d2_lines.append('    fill: "#FFD700"')
                d2_lines.append('    stroke: "#FF8C00"')
                d2_lines.append("  }")
                d2_lines.append("}")
                d2_lines.append("")

                # Add condition branches for decision instances
                for condition in inst.get("conditionAssignments", []):
                    condition_text = condition["condition"].replace('"', '\\"')
                    target_id = condition["conditionTargetId"]
                    d2_lines.append(f'{inst["id"]} -> {target_id}: "{condition_text}"')
                    d2_lines.append("")

            # Add exit node
            if instances:
                last_instance = instances[-1]
                exit_obj = self._get_cross_reference(
                    last_instance.get("timelineExitId")
                )
                if exit_obj:
                    d2_lines.append(f'{exit_obj["id"]}: "Exit" {{')
                    d2_lines.append("  shape: oval")
                    d2_lines.append("  width: 100")
                    d2_lines.append("  height: 60")
                    d2_lines.append("  style: {")
                    d2_lines.append('    fill: "#FFB6C1"')
                    d2_lines.append('    stroke: "#DC143C"')
                    d2_lines.append("    stroke-width: 2")
                    d2_lines.append("  }")
                    d2_lines.append("}")
                    d2_lines.append("")

                    # Connect last activity instance to exit
                    if activity_instances:
                        d2_lines.append(
                            f"{activity_instances[-1]['id']} -> {exit_obj['id']}: exit"
                        )
                        d2_lines.append("")

            # Add timing nodes
            for timing in timings:
                timing_label = f"{timing.label}\\n{timing.type.decode}\\n{timing.value}\\n{timing.windowLower}..{timing.windowUpper}"
                timing_label = timing_label.replace('"', '\\"')
                d2_lines.append(f'{timing.id}: "{timing_label}" {{')
                d2_lines.append("  shape: circle")
                d2_lines.append("  style: {")
                d2_lines.append('    fill: "#DDA0DD"')
                d2_lines.append('    stroke: "#8B008B"')
                d2_lines.append("  }")
                d2_lines.append("}")
                d2_lines.append("")

                from_id = timing.relativeFromScheduledInstanceId
                to_id = timing.relativeToScheduledInstanceId

                d2_lines.append(f"{from_id} -> {timing.id}: from")
                d2_lines.append(f"{timing.id} -> {to_id}: to")
                d2_lines.append("")

            return "\n".join(d2_lines)
        except Exception as e:
            self._errors.exception(
                f"Failed generating D2 for timeline {timeline.label}", e
            )
            return ""

    def _get_cross_reference(self, id):
        return self._builder._data_store.instance_by_id(id)


def save_d2(file_path, content):
    """Save D2 content to file."""
    with open(file_path, "w") as f:
        f.write(content)


def render_d2_to_svg(d2_file, svg_file):
    """Render D2 file to SVG using the d2 command."""
    try:
        # Check if d2 is installed
        result = subprocess.run(["which", "d2"], capture_output=True, text=True)
        if result.returncode != 0:
            print("\nWarning: D2 is not installed.")
            print("To install D2, visit: https://d2lang.com/tour/install")
            print("Or use: brew install d2 (on macOS)")
            print(f"\nD2 source file has been created: {d2_file}")
            return False

        # Render the diagram
        print(f"Rendering D2 diagram to {svg_file}...")
        subprocess.run(["d2", d2_file, svg_file], check=True)
        print(f"Successfully created: {svg_file}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error rendering D2 diagram: {e}")
        return False


def sanitize_filename(name):
    """Sanitize a string to be used as a filename."""
    # Replace problematic characters with underscores
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")
    # Remove leading/trailing spaces and dots
    name = name.strip(". ")
    # Limit length
    if len(name) > 100:
        name = name[:100]
    return name if name else "timeline"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="USDM Timeline to D2 Program",
        description="Will display USDM timelines using D2 - creates separate SVG for each timeline",
        epilog="Generates D2 diagram and SVG output for each timeline",
    )
    parser.add_argument("filename", help="The name of the USDM JSON file.")
    args = parser.parse_args()
    filename = args.filename

    input_path, tail = os.path.split(filename)
    root_filename = tail.replace(".json", "")
    full_filename = filename
    output_path = input_path if input_path else "."

    print("")
    print(f"Input file: {full_filename}")
    print(f"Output path: {output_path}")
    print("")

    errors = Errors()
    timeline_processor = Timeline(full_filename, errors)
    timelines = timeline_processor.get_timelines()

    if errors.error_count() > 0:
        print(f"Errors: {errors.dump(0)}")
    elif not timelines:
        print("No timelines found in the input file.")
    else:
        print(f"Found {len(timelines)} timeline(s)")
        print("")

        for idx, timeline in enumerate(timelines, 1):
            # Create filename based on timeline label
            timeline_name = sanitize_filename(timeline.label)
            d2_output_file = os.path.join(
                output_path, f"{root_filename}_{timeline_name}.d2"
            )
            svg_output_file = os.path.join(
                output_path, f"{root_filename}_{timeline_name}.svg"
            )

            print(f"[{idx}/{len(timelines)}] Processing timeline: {timeline.label}")

            # Generate D2 content for this timeline
            d2_content = timeline_processor.generate_timeline_d2(timeline)

            if d2_content:
                save_d2(d2_output_file, d2_content)
                print(f"  ✓ D2 file: {d2_output_file}")

                if render_d2_to_svg(d2_output_file, svg_output_file):
                    print(f"  ✓ SVG file: {svg_output_file}")
                else:
                    print(
                        f"  → You can render manually: d2 {d2_output_file} {svg_output_file}"
                    )
            else:
                print(f"  ✗ Failed to generate D2 content")

            print("")

        print(f"Completed processing {len(timelines)} timeline(s)")
        if errors.error_count() > 0:
            print(f"Errors encountered: {errors.dump(0)}")
