import os
import argparse
from bs4 import BeautifulSoup
from yattag import Doc
from uuid import uuid4
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
                                    checkbox_html = '''
                                    <div class="d-flex align-items-start gap-3">
                                        <div class="flex-grow-1">
                                            <strong>IN{identifier}:</strong> {text}
                                        </div>
                                        <div class="btn-group btn-group-sm" role="group">
                                            <input type="checkbox" class="btn-check" id="in{identifier}-yes" autocomplete="off">
                                            <label class="btn btn-outline-success" for="in{identifier}-yes">
                                                <i class="bi bi-check-lg"></i> Yes
                                            </label>
                                            <input type="checkbox" class="btn-check" id="in{identifier}-no" autocomplete="off">
                                            <label class="btn btn-outline-danger" for="in{identifier}-no">
                                                <i class="bi bi-x-lg"></i> No
                                            </label>
                                        </div>
                                    </div>
                                    '''.format(identifier=ec["identifier"], text=eci["text"])
                                    results["Inclusion Criteria"].append(checkbox_html)
                                if ec["category"]["code"] == "C25370":
                                    eci = data_store.instance_by_id(ec["criterionItemId"])
                                    checkbox_html = '''
                                    <div class="d-flex align-items-start gap-3">
                                        <div class="flex-grow-1">
                                            <strong>EX{identifier}:</strong> {text}
                                        </div>
                                        <div class="btn-group btn-group-sm" role="group">
                                            <input type="checkbox" class="btn-check" id="ex{identifier}-yes" autocomplete="off">
                                            <label class="btn btn-outline-success" for="ex{identifier}-yes">
                                                <i class="bi bi-check-lg"></i> Yes
                                            </label>
                                            <input type="checkbox" class="btn-check" id="ex{identifier}-no" autocomplete="off">
                                            <label class="btn btn-outline-danger" for="ex{identifier}-no">
                                                <i class="bi bi-x-lg"></i> No
                                            </label>
                                        </div>
                                    </div>
                                    '''.format(identifier=ec["identifier"], text=eci["text"])
                                    results["Exclusion Criteria"].append(checkbox_html)
                        else:
                            results[key] = []
                            
        for k, v in results.items():
            if not v:
                v.append("Some instructions here ...")
        return label, results


    def _generate_html(self, label: str, data: dict):
        doc = Doc()
        with doc.tag(f"div", klass="container-fluid px-4"):
            with doc.tag(f"div", klass="row g-3"):
                for k, v in data.items():
                    with doc.tag(f"div", klass="col-12"):
                        with doc.tag(f"div", klass="card shadow-sm border-0"):
                            with doc.tag(f"div", klass="card-header bg-primary text-white py-2"):
                                with doc.tag(f"h5", klass="mb-0"):
                                    doc.asis(f"{k}")
                            with doc.tag(f"div", klass="card-body p-3"):                            
                                for item in v:
                                    with doc.tag(f"p", klass="card-text mb-2 small"):
                                        doc.asis(f"{item}")

        # Generate HTML
        html = f"""<!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>USDM Visit - {label}</title>
                    <link href="https://bootswatch.com/5/zephyr/bootstrap.min.css" rel="stylesheet">
                    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
                    <style>
                        body {{
                            background-color: #f8f9fa;
                            font-size: 0.9rem;
                        }}
                        .page-header {{
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 1.5rem 0;
                            margin-bottom: 1.5rem;
                            border-radius: 0;
                        }}
                        .card {{
                            transition: transform 0.2s;
                        }}
                        .card:hover {{
                            transform: translateY(-2px);
                        }}
                        .card-header {{
                            font-weight: 500;
                            letter-spacing: 0.3px;
                        }}
                        .btn-group-sm .btn {{
                            min-width: 60px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="page-header">
                        <div class="container-fluid px-4">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-calendar-check me-2" style="font-size: 1.5rem;"></i>
                                <div>
                                    <h2 class="mb-0">{label} Visit</h2>
                                </div>
                            </div>
                        </div>
                    </div>
                    {doc.getvalue()}
                    <div class="container-fluid px-4 py-3">
                        <small class="text-muted">Generated with USDM4 Utility</small>
                    </div>
                </body>
            </html>
        """
        return html

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
