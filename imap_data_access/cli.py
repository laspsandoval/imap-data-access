#!/usr/bin/env python3

"""Command line interface to the IMAP Data Access API.

This module serves as a command line utility to invoke the IMAP Data Access API.
It provides the ability to interact with the Science Data Center (SDC)
by querying, downloading, and uploading files to the data center.

Use
---
    imap-data-access <command> [<args>]
    imap-data-access --help
    imap-data-access download <file_path>
    imap-data-access query <query-parameters>
    imap-data-access upload <file_path>
"""
import argparse
import logging
import os
from pathlib import Path

import imap_data_access


def _download_parser(args: argparse.Namespace):
    """Download a file from the IMAP SDC.

    Parameters
    ----------
    args : argparse.Namespace
        An object containing the parsed arguments and their values
    """
    try:
        output_path = imap_data_access.download(args.file_path)
        print(f"Successfully downloaded the file to: {output_path}")
    except imap_data_access.io.IMAPDataAccessError as e:
        print(e)


def _print_query_results_table(query_results):
    """Print the query results in a table.

    Parameters
    ----------
    query_results : list
        A list of dictionaries containing the query results
    """
    num_files = len(query_results)
    print(f"Found [{num_files}] matching files")
    if num_files == 0:
        return
    format_string = "{:<10}|{:<10}|{:<10}|{:<10}|{:<8}|{:<7}|{:<50}|"
    # Add hyphens for a separator between header and data
    hyphens = "-" * 111 + "|"
    print(hyphens)
    header = [
        "Instrument",
        "Data Level",
        "Descriptor",
        "Start Date",
        "End Date",
        "Version",
        "Filename",
    ]
    print(format_string.format(*header))
    print(hyphens)

    # Print data
    for item in query_results:
        values = [
            item["instrument"],
            item["data_level"],
            item["descriptor"],
            item["start_date"],
            item["end_date"],
            item["version"],
            os.path.basename(item["file_path"]),
        ]
        print(format_string.format(*values))
    # Close the table
    print(hyphens)


def _query_parser(args: argparse.Namespace):
    """Query the IMAP SDC.

    Parameters
    ----------
    args : argparse.Namespace
        An object containing the parsed arguments and their values
    """
    # Filter to get the arguments of interest from the namespace
    valid_args = [
        "instrument",
        "data_level",
        "descriptor",
        "start_date",
        "end_date",
        "version",
        "extension",
    ]
    query_params = {
        key: value
        for key, value in vars(args).items()
        if key in valid_args and value is not None
    }
    try:
        query_results = imap_data_access.query(**query_params)
    except imap_data_access.io.IMAPDataAccessError as e:
        print(e)
        return

    if args.output_format == "table":
        _print_query_results_table(query_results)
    elif args.output_format == "json":
        # Dump the content directly
        print(query_results)


def _upload_parser(args: argparse.Namespace):
    """Upload a file to the IMAP SDC.

    Parameters
    ----------
    args : argparse.Namespace
        An object containing the parsed arguments and their values
    """
    try:
        imap_data_access.upload(args.file_path)
        print("Successfully uploaded the file to the IMAP SDC")
    except imap_data_access.io.IMAPDataAccessError as e:
        print(e)


def main():
    """Parse the command line arguments.

    Run the command line interface to the IMAP Data Access API.
    """
    description = (
        "This command line program accesses the IMAP SDC APIs to query, download, "
        "and upload data files."
    )
    data_dir_help = (
        "Directory to use for reading and writing IMAP data. "
        "The default is a 'data/' folder in the "
        "current working directory. This can also be "
        "set using the IMAP_DATA_DIR environment variable."
    )
    url_help = (
        "URL of the IMAP SDC API. "
        "The default is https://api.dev.imap-mission.com. This can also be "
        "set using the IMAP_DATA_ACCESS_URL environment variable."
    )
    download_help = (
        "Download a file from the IMAP SDC to the locally configured data directory. "
        "This must be the full path to the file."
        "\nE.g. imap/mag/l0/2025/01/imap_mag_l0_raw_20250101_20250101_v00-00.pkts"
    )
    query_help = (
        "Query the IMAP SDC for files matching the query parameters. "
        "The query parameters are optional, but at least one must be provided."
    )
    upload_help = (
        "Upload a file to the IMAP SDC. This must be the full path to the file."
        "\nE.g. imap/mag/l0/2025/01/imap_mag_l0_raw_20250101_20250101_v00-00.pkts"
    )

    parser = argparse.ArgumentParser(prog="imap-data-access", description=description)
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {imap_data_access.__version__}",
    )
    parser.add_argument("--data-dir", type=Path, required=False, help=data_dir_help)
    parser.add_argument("--url", type=str, required=False, help=url_help)
    # Logging level
    parser.add_argument(
        "--debug",
        help="Print lots of debugging statements",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Add verbose output",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
    )

    # Download command
    subparsers = parser.add_subparsers(required=True)
    parser_download = subparsers.add_parser("download")
    parser_download.add_argument("file_path", type=Path, help=download_help)
    parser_download.set_defaults(func=_download_parser)

    # Query command (with optional arguments)
    query_parser = subparsers.add_parser("query", help=query_help)
    query_parser.add_argument(
        "--instrument",
        type=str,
        required=False,
        help="Name of the instrument",
        choices=[
            "codice",
            "glows",
            "hi",
            "hit",
            "idex",
            "lo",
            "mag",
            "swapi",
            "swe",
            "ultra",
        ],
    )
    query_parser.add_argument(
        "--data-level",
        type=str,
        required=False,
        help="Data level of the product (l0, l1a, l2, etc.)",
    )
    query_parser.add_argument(
        "--descriptor",
        type=str,
        required=False,
        help="Descriptor of the product (raw, burst, etc.)",
    )
    query_parser.add_argument(
        "--start-date", type=str, required=False, help="Start date in YYYYMMDD format"
    )
    query_parser.add_argument(
        "--end-date", type=str, required=False, help="End date in YYYYMMDD format"
    )
    query_parser.add_argument(
        "--version",
        type=str,
        required=False,
        help="Version of the product in the format 'v00-00'",
    )
    query_parser.add_argument(
        "--extension", type=str, required=False, help="File extension (cdf, pkts, etc.)"
    )
    query_parser.add_argument(
        "--output-format",
        type=str,
        required=False,
        help="How to format the output, default is 'table'",
        choices=["table", "json"],
        default="table",
    )
    query_parser.set_defaults(func=_query_parser)

    # Upload command
    parser_upload = subparsers.add_parser("upload")
    parser_upload.add_argument("file_path", type=Path, help=upload_help)
    parser_upload.set_defaults(func=_upload_parser)

    # Parse the arguments and set the values
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    if args.data_dir:
        # We got an explicit data directory from the command line
        data_path = args.data_dir.resolve()
        if not data_path.exists():
            raise ValueError(f"Data directory {args.data_dir} does not exist")
        # Set the data directory to the user-supplied value
        imap_data_access.config["DATA_DIR"] = data_path

    if args.url:
        # We got an explicit url from the command line
        imap_data_access.config["DATA_ACCESS_URL"] = args.url

    # Now process through the respective function for the invoked command
    # (set with set_defaults on the subparsers above)
    args.func(args)


if __name__ == "__main__":
    main()
