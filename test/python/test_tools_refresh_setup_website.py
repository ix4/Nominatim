"""
Tests for setting up the website scripts.
"""
import subprocess

import pytest

from nominatim.tools import refresh

@pytest.fixture
def test_script(tmp_path):
    (tmp_path / 'php').mkdir()

    website_dir = (tmp_path / 'php' / 'website')
    website_dir.mkdir()

    def _create_file(code):
        outfile = website_dir / 'reverse-only-search.php'
        outfile.write_text('<?php\n{}\n'.format(code), 'utf-8')

    return _create_file


@pytest.fixture
def run_website_script(tmp_path, def_config, temp_db_conn):
    def_config.lib_dir.php = tmp_path / 'php'
    def_config.project_dir = tmp_path

    def _runner():
        refresh.setup_website(tmp_path, def_config, temp_db_conn)

        proc = subprocess.run(['/usr/bin/env', 'php', '-Cq',
                               tmp_path / 'search.php'], check=False)

        return proc.returncode

    return _runner


@pytest.mark.parametrize("setting,retval", (('yes', 10), ('no', 20)))
def test_setup_website_check_bool(monkeypatch, test_script, run_website_script,
                                  setting, retval):
    monkeypatch.setenv('NOMINATIM_CORS_NOACCESSCONTROL', setting)

    test_script('exit(CONST_NoAccessControl ? 10 : 20);')

    assert run_website_script() == retval


@pytest.mark.parametrize("setting", (0, 10, 99067))
def test_setup_website_check_int(monkeypatch, test_script, run_website_script, setting):
    monkeypatch.setenv('NOMINATIM_LOOKUP_MAX_COUNT', str(setting))

    test_script('exit(CONST_Places_Max_ID_count == {} ? 10 : 20);'.format(setting))

    assert run_website_script() == 10


def test_setup_website_check_empty_str(monkeypatch, test_script, run_website_script):
    monkeypatch.setenv('NOMINATIM_DEFAULT_LANGUAGE', '')

    test_script('exit(CONST_Default_Language === false ? 10 : 20);')

    assert run_website_script() == 10


def test_setup_website_check_str(monkeypatch, test_script, run_website_script):
    monkeypatch.setenv('NOMINATIM_DEFAULT_LANGUAGE', 'ffde 2')

    test_script('exit(CONST_Default_Language === "ffde 2" ? 10 : 20);')

    assert run_website_script() == 10
