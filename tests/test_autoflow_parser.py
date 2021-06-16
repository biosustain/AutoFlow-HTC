#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `autoflow_parser` package."""

from os import pardir
from os.path import join, abspath
from click.testing import CliRunner
import tecan_od_analyzer.tecan_od_analyzer
from tecan_od_analyzer.cli.cli import cli


def test_command_line_interface():
    """Test the CLI."""

    runner = CliRunner()

    # autoflow_parser path
    afpp = abspath(join(tecan_od_analyzer.__path__[0], pardir))
    print(join(afpp, 'data', 'ExampleFiles_Cultivation1'))
    # check test paths
    for path in [join(afpp, 'data', 'ExampleFiles_Cultivation1'),
                 join(afpp, 'data', 'ExampleFiles_Cultivation2')]:
        result = runner.invoke(cli.main, ["--path", path])
        assert result.exit_code == 0

    # check faulty path
    result = runner.invoke(cli.main, ["--path", join(afpp, 'not_a_path')])
    assert result.exit_code == -1
    assert "Given path doesn't exist:" in result.output

    # check path with missing files
    result = runner.invoke(cli.main, ["--path", afpp])
    assert result.exit_code == -1
    assert "\"Logfile.txt\" doesn't exist in:" in result.output
