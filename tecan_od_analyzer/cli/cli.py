# -*- coding: utf-8 -*-

"""Console script for autoflow_parser."""
import sys
import click
import os
import pandas as pd

from tecan_od_analyzer.autoflow_parser.autoflow_parser import (
    process_logfile,
    check_results_files,
    merge_results,
    make_channel_dfs,
)


def main(path, max_timeflex):
    """Console script for autoflow_parser."""
    # Check given path
    if not os.path.exists(path):
        click.echo("Given path doesn't exist:\n" f'"{path}"')
        sys.exit(-1)
    path = os.path.abspath(path)

    # Check files in path
    files = set(os.listdir(path))
    print(files)
    if "Logfile.txt" not in files:
        click.echo('"Logfile.txt" doesn\'t exist in:\n' f'"{path}"')
        sys.exit(-1)
    else:
        # click.echo(f"Logfile found...")
        click.echo("Logfile found...")
        files.remove("Logfile.txt")

    (status, entries) = process_logfile(path)
    if status == -1:
        click.echo(entries)
        sys.exit(-1)
    else:
        click.echo(f"\t... and contains {len(entries)} entries.")

    (
        timeflex,
        missing_files,
        multiple_matches,
        entry_to_file,
        files,
    ) = check_results_files(entries, files, max_timeflex)
    if not missing_files and not multiple_matches:
        click.echo(
            f"\t... and all entries are matched with files using "
            f"{timeflex} seconds as timeflex."
        )
        if len(files) > 1:
            # click.echo(f"Other files in path are ignored:\n\t" +
            #            "\n\t".join([file for file in files]))
            click.echo(
                "Other files in path are ignored:\n\t"
                + "\n\t".join([file for file in files])
            )
    else:
        if multiple_matches:
            click.echo(
                "Multiple files may match following entries:\n\t"
                + "\n\t".join(
                    [
                        f"{entry}: {','.join(matches)}"
                        for entry, matches in entry_to_file.items()
                        if type(matches) is set
                    ]
                )
            )
        if missing_files:
            click.echo(
                "Missing files for the following entries:\n\t"
                + "\n\t".join(
                    [
                        entry
                        for entry, matches in entry_to_file.items()
                        if matches == ""
                    ]
                )
                + "\nLarger 'max_timeflex' may help, if there aren't "
                "entries matched with multiple files."
            )
        sys.exit(-1)

    # Collect results in this dictionary.
    result_dfs = dict()

    click.echo("Parsing and merging Tecan files...")
    # TODO: a status bar here would be nice
    result_dfs["collected_measurements"] = merge_results(entry_to_file, path)
    click.echo("\t... done.")

    # split merged results and reformat for easy plotting in excel
    click.echo("Reformating collected files...")
    result_dfs.update(make_channel_dfs(result_dfs["collected_measurements"]))
    click.echo("\t... done.")

    # TODO: remove this. meant to be only temporary.
    # TODO: also a version to handle existing result file would be nice
    click.echo("Writing results...")
    writer = pd.ExcelWriter("results.xlsx")
    for key, value in result_dfs.items():
        value.to_excel(writer, sheet_name=key)
    writer.save()
    click.echo("\t... done.")
    return
    # sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
