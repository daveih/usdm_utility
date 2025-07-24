import os
import argparse
from uuid import uuid4
from yattag import Doc
from bs4 import BeautifulSoup
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
    FULL = "full"
    BODY = "body"

    def __init__(self, file_path: str, errors: Errors):
        self._errors = errors
        self._usdm = USDM4()
        self._file_path = file_path
        self._builder: Builder = self._usdm.builder()

    def to_html(self, level=FULL):
        self._builder.seed(self._file_path)
        wrapper_dict: dict = self._builder._data_store.data
        wrapper_dict['study']['id'] = uuid4()
        wrapper = Wrapper.model_validate(wrapper_dict)
        try:
            doc = Doc()
            study_design = wrapper.study.versions[0].studyDesigns[0]
            if level == self.BODY:
                self._body(doc, study_design)
            else:
                self._full(doc, study_design)
            return doc.getvalue()
        except Exception as e:
            self._errors.exception(
                f"Failed generating HTML page at level '{level}'", e
            )
            return ""

    def _full(self, doc, study_design: StudyDesign):
        doc.asis("<!DOCTYPE html>")
        with doc.tag("html"):
            with doc.tag("head"):
                doc.asis('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">')
                doc.asis('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">')
          
            with doc.tag("body"):
                self._body(doc, study_design)

    def _body(self, doc, study_design: StudyDesign):
        for timeline in study_design.scheduleTimelines:
            timings = timeline.timings
            with doc.tag(f"main", klass="container"):
                with doc.tag(f"h1", klass="mt-5"):
                    doc.asis(f"{timeline.name}")
                with doc.tag("pre", klass="mermaid"):
                    #doc.asis("\ngraph LR\n")
                    doc.asis("\ngraph TD\n")
                    doc.asis(f"{timeline.id}([{timeline.entryCondition}])\n")
                    instance = self._get_cross_reference(timeline.entryId)
                    if instance['instanceType'] == ScheduledActivityInstance.__name__:
                        doc.asis(f"{instance['id']}(ScheduledActivityInstance)\n")
                    else:
                        doc.asis(f"{instance['id']}{{{{ScheduledDecisionInstance}}}}\n")
                    doc.asis(f"{timeline.id} -->|first| {instance['id']}\n")
                    prev_instance = instance
                    instance = self._get_cross_reference(instance['defaultConditionId'])
                    while instance:
                        if instance['instanceType'] == ScheduledActivityInstance.__name__:
                            doc.asis(f"{instance['id']}(ScheduledActivityInstance)\n")
                        else:
                            doc.asis(f"{instance['id']}{{{{ScheduledDecisionInstance}}}}\n")
                            for condition in instance['conditionAssignments']:
                                doc.asis(
                                    f"{instance['id']} -->|{condition['condition']}| {condition['conditionTargetId']}\n"
                                )
                        doc.asis(f"{prev_instance['id']} -->|default| {instance['id']}\n")
                        prev_instance = instance
                        instance = self._get_cross_reference(
                            prev_instance['defaultConditionId']
                        )
                    exit = self._get_cross_reference(prev_instance['timelineExitId'])
                    doc.asis(f"{exit['id']}([Exit])\n")
                    doc.asis(f"{prev_instance['id']} -->|exit| {exit['id']}\n")
                    for timing in timings:
                        doc.asis(
                            f"{timing.id}(({timing.label}\n{timing.type.decode}\n{timing.value}\n{timing.windowLower}..{timing.windowUpper}))\n"
                        )
                        doc.asis(
                            f"{timing.relativeFromScheduledInstanceId} -->|from| {timing.id}\n"
                        )
                        doc.asis(
                            f"{timing.id} -->|to| {timing.relativeToScheduledInstanceId}\n"
                        )
        with doc.tag("script", type="module"):
            doc.asis(
                "import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';\n"
            )
            doc.asis("mermaid.initialize({ startOnLoad: true });\n")

    def _get_cross_reference(self, id):
        return self._builder._data_store.instance_by_id(id)

def save_html(file_path, result):
    soup = BeautifulSoup(result, "html.parser")
    data = soup.prettify()
    with open(file_path, "w") as f:
        f.write(data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='USDM Simple Timeline Program',
        description='Will display USDM timelines using Mermaid',
        epilog='Note: Not that sophisticated! :)'
    )
    parser.add_argument('filename', help="The name of the USDM USDM file.") 
    args = parser.parse_args()
    filename = args.filename
    
    input_path, tail = os.path.split(filename)
    root_filename = tail.replace(".json", "")
    full_filename = filename
    output_path = input_path
    full_output_filename = os.path.join(output_path, f"{root_filename}.html")

    print("")
    print(f"Output path is: {output_path}")
    print(f"Output file is: {full_output_filename}")
    print("")
    errors = Errors()
    timeline = Timeline(full_filename, errors)
    html = timeline.to_html()
    print(f"Errors: {errors.dump(0)}")
    save_html(full_output_filename, html)
