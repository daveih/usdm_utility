import os
import argparse
import warnings
from bs4 import BeautifulSoup
from yattag import Doc
from usdm4 import USDM4
from usdm4.builder.builder import Builder, DataStore
from simple_error_log.errors import Errors


class IE:
    def __init__(self, file_path: str, errors: Errors):
        self._errors = errors
        self._usdm = USDM4()
        self._file_path = file_path
        self._builder: Builder = self._usdm.builder(errors)

    def to_html(self) -> str:
        try:
            self._builder.seed(self._file_path)
            inc, exc = self._ie_data()
            return self._generate_html(inc, exc)
        except Exception as e:
            self._errors.exception(f"Failed generating HTML page", e)
            return ""

    def _ie_data(self) -> tuple[list, list]:
        self._data_store: DataStore = self._builder._data_store
        inclusion = []
        exclusion = []
        for ec in self._data_store.instances_by_klass(
            "EligibilityCriterion"
        ):
            eci = self._data_store.instance_by_id(
                ec["criterionItemId"]
            )
            translated_text = self._translate_references(
                eci, eci["text"]
            )
            if ec["category"]["code"] == "C25532":
                inclusion.append({"identifier": ec["identifier"], "text": translated_text})
            if ec["category"]["code"] == "C25370":
                exclusion.append({"identifier": ec["identifier"], "text": translated_text})
        return inclusion, exclusion

    def _generate_html(self, inclusion: str, exclusion: str):
        doc = Doc()
        with doc.tag(f"div", klass="container-fluid px-4 times-new-roman"):
            with doc.tag("div", klass="row g-3"):
                with doc.tag("div", klass="col-12"):
                    with doc.tag("h2", klass=""):
                        doc.asis("5.2 Inclusion Criteria")
                    with doc.tag("p", klass=""):
                        doc.asis("To be eligible to participate in this trial, an individual must meet all the following criteria:")
                    self._ie_table(doc, inclusion)
                    with doc.tag(f"h2", klass=""):
                        doc.asis("5.3 Exclusion Criteria")
                    with doc.tag(f"p", klass=""):
                        doc.asis("An individual who meets any of the following criteria will be excluded from participation in this trial:")
                    self._ie_table(doc, exclusion)

        # Generate HTML
        html = f"""<!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>USDM to M11 Inclusion & Exclusion</title>
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
                        .times-new-roman,
                        .times-new-roman * {{
                            font-family: 'Times New Roman', Times, serif !important;
                        }}
                        .times-new-roman h2 {{
                            font-size: 14pt;
                            font-weight: bold;
                        }}
                    </style>
                </head>
                <body>
                    {doc.getvalue()}
                    <div class="container-fluid px-4 py-3">
                        <small class="text-muted">Generated with USDM4 Utility</small>
                    </div>
                </body>
            </html>
        """
        return html

    def _ie_table(self, doc, criteria: list):
        with doc.tag("table"):
            for c in criteria:
                with doc.tag("tr"):
                    with doc.tag("td"):
                        doc.asis(f"{c['identifier']}:")
                    with doc.tag("td"):
                        doc.asis(f"{c['text']}")

    def _translate_references(self, instance: dict, text: str) -> str:
        text = self._wrap_tag(text, "u")
        text = self._wrap_tag(text, "i")
        return self._translate_references_recurse(instance, text)

    def _wrap_tag(self, text: str, tag: str) -> str:
        soup = self._get_soup(text)
        for ref in soup(["usdm:ref", "usdm:tag"]):
            ref.wrap(soup.new_tag(tag))
        return str(soup)

    def _translate_references_recurse(self, instance: dict, text: str) -> str:
        # print(f"LEVEL: {text}")
        soup = self._get_soup(text)
        for ref in soup(["usdm:ref", "usdm:tag"]):
            try:
                if ref.name == "usdm:ref":
                    text = self._resolve_usdm_ref(instance, ref)
                    ref.replace_with(self._translate_references_recurse(instance, text))
                if ref.name == "usdm:tag":
                    text = self._resolve_usdm_tag(instance, ref)
                    ref.replace_with(self._translate_references_recurse(instance, text))
            except Exception as e:
                errors.exception(
                    f"Exception raised while attempting to translate '{ref}' while generating the HTML document, see the logs for more info",
                    e,
                )
        return str(soup)

    def _resolve_usdm_ref(self, instance, ref) -> str:
        attributes = ref.attrs
        instance = self._data_store.instance_by_id(attributes["id"])
        value = str(instance[attributes["attribute"]])
        return value

    def _resolve_usdm_tag(self, instance, ref) -> str:
        attributes = ref.attrs
        dictionary = self._data_store.instance_by_id(instance["dictionaryId"])
        if dictionary:
            for p_map in dictionary["parameterMaps"]:
                if p_map["tag"] == attributes["name"]:
                    value = p_map["reference"]
                    return value
        return f"<i>missing dictionary reference</i>"

    def _get_soup(self, text: str):
        try:
            with warnings.catch_warnings(record=True) as warning_list:
                result = BeautifulSoup(text, "html.parser")
                if warning_list:
                    for item in warning_list:
                        errors.debug(
                            f"Warning raised within Soup package, processing '{text}'\nMessage returned '{item.message}'"
                        )
                return result
        except Exception as e:
            errors.exception(f"Parsing '{text}' with soup", e)
            return ""


def save_html(file_path, result):
    soup = BeautifulSoup(result, "html.parser")
    data = soup.prettify()
    with open(file_path, "w") as f:
        f.write(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="USDM Simple Visit Program",
        description="Will display USDM visits",
        epilog="Note: Not that sophisticated! :)",
    )
    parser.add_argument("filename", help="The name of the USDM file.")
    args = parser.parse_args()
    filename = args.filename

    input_path, tail = os.path.split(filename)
    root_filename = tail.replace(".json", "")
    full_filename = filename
    output_path = input_path
    full_output_filename = os.path.join(output_path, f"{root_filename}_criterion.html")

    print("")
    print(f"Output path is: {output_path}")
    print(f"Output file is: {full_output_filename}")
    print("")
    errors = Errors()
    ie = IE(full_filename, errors)
    html = ie.to_html()
    print(f"Errors: {errors.dump(0)}")
    save_html(full_output_filename, html)
