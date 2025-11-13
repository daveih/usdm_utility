import os
import argparse
import json
from bs4 import BeautifulSoup
from yattag import Doc
from uuid import uuid4
from usdm4.api.scheduled_instance import (
    ScheduledActivityInstance,
    ScheduledDecisionInstance,
)
from usdm4.api.wrapper import Wrapper
from usdm4.api.study_design import StudyDesign
from usdm4 import USDM4
from usdm4.builder.builder import Builder, DataStore
from simple_error_log.errors import Errors


class Visit:

    def __init__(self, file_path: str, errors: Errors):
        self._errors = errors
        self._usdm = USDM4()
        self._file_path = file_path
        self._builder: Builder = self._usdm.builder(errors)

    def to_html(self, visit_id: str) -> str:
        try:
            self._builder.seed(self._file_path)
            # wrapper_dict: dict = self._data_store.data
            # wrapper = Wrapper.model_validate(wrapper_dict)
            # study_design = wrapper.study.versions[0].studyDesigns[0]
            label, visit_data = self._visit_data(visit_id)
            return self._generate_html(label, visit_data)
        except Exception as e:
            self._errors.exception(
                f"Failed generating HTML page", e
            )
            return ""

    def _visit_data(self, visit_id: str) -> tuple[str, dict]:
        results = {}
        label = "Not Found"
        data_store: DataStore = self._builder._data_store
        encounter = next((x for x in data_store.instances_by_klass("Encounter") if x["id"] == visit_id), None)
        if encounter:
            label = encounter["label"]
            timepoint = next((x for x in data_store.instances_by_klass("ScheduledActivityInstance") if x["encounterId"] == encounter["id"]), None)
            if timepoint:
                for id in timepoint["activityIds"]:
                    activity = data_store.instance_by_id(id)
                    key = activity["label"]
                    if key not in results:
                        if activity["label"].startswith("Inclusion"):
                            results["Inclusion Criteria"] = []
                            results["Exclusion Criteria"] = []
                            for ec in data_store.instances_by_klass("EligibilityCriterion"):
                                print(f"EC: {ec}")
                                if ec["category"]["code"] == "C25532":
                                    eci = data_store.instance_by_id(ec["criterionItemId"])
                                    results["Inclusion Criteria"].append(f"<strong>IN{ec["identifier"]}:</strong> {eci["text"]}")
                                if ec["category"]["code"] == "C25370":
                                    eci = data_store.instance_by_id(ec["criterionItemId"])
                                    results["Exclusion Criteria"].append(f"<strong>EX{ec["identifier"]}:</strong> {eci["text"]}")
                        else:
                            results[key] = []
                            
        for k, v in results.items():
            if not v:
                v.append("Some instructions here ...")
        return label, results


    def _generate_html(self, label: str, data: dict):
        doc = Doc()
        with doc.tag(f"div", klass="container-fluid"):
            with doc.tag(f"div", klass="col mt-3"):
                for k, v in data.items():
                    with doc.tag(f"div", klass="card rounded-3"):
                        with doc.tag(f"div", klass="card-header"):
                            with doc.tag(f"h4", klass="mt-5"):
                                doc.asis(f"{k}")
                            with doc.tag(f"div", klass="card-body"):                            
                                for item in v:
                                    with doc.tag(f"p", klass="card-text"):
                                        doc.asis(f"{item}")

        # Generate HTML
        html = f"""<!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>USDM Visit Visualization for {label}</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
                </head>
                <body>
                    <div class="container-fluid">
                        <h1>USDM Visit Visualization for {label}</h1>
                        {doc.getvalue()}
                    </div>
                </body>
            </html>
        """
        return html

def save_html(file_path, result):
    """Save HTML content to file."""
    with open(file_path, "w") as f:
        f.write(result)


def save_html(file_path, result):
    soup = BeautifulSoup(result, "html.parser")
    data = soup.prettify()
    with open(file_path, "w") as f:
        f.write(data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='USDM Simple Visit Program',
        description='Will display USDM visits',
        epilog='Note: Not that sophisticated! :)'
    )
    parser.add_argument('filename', help="The name of the USDM file.") 
    parser.add_argument('id', help="The id for the visit.") 
    args = parser.parse_args()
    filename = args.filename
    id = args.id
    
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
    timeline = Visit(full_filename, errors)
    html = timeline.to_html(id)
    print(f"Errors: {errors.dump(0)}")
    save_html(full_output_filename, html)