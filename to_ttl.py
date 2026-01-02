#!/usr/bin/env python3
"""Convert RDF/XML file to Turtle (.ttl) format."""

import argparse
import sys
from pathlib import Path

from rdflib import Graph


def convert_rdf_to_ttl(input_path: str, output_path: str | None = None) -> None:
    """Convert an RDF/XML file to Turtle format.

    Args:
        input_path: Path to the input RDF/XML file.
        output_path: Path for the output .ttl file. If None, derives from input.
    """
    input_file = Path(input_path)

    if not input_file.exists():
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    if output_path is None:
        output_file = input_file.with_suffix('.ttl')
    else:
        output_file = Path(output_path)

    g = Graph()
    g.parse(input_file, format='xml')
    g.serialize(destination=output_file, format='turtle')

    print(f"Converted '{input_file}' to '{output_file}'")


def main():
    parser = argparse.ArgumentParser(
        description='Convert RDF/XML file to Turtle (.ttl) format.'
    )
    parser.add_argument('input', help='Input RDF/XML file')
    parser.add_argument('-o', '--output', help='Output .ttl file (default: same name with .ttl extension)')

    args = parser.parse_args()
    convert_rdf_to_ttl(args.input, args.output)


if __name__ == '__main__':
    main()
