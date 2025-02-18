#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''The omegaUp i18n linter.'''

import collections
import json
import os
import re
import sys

from typing import (DefaultDict, Dict, List, Mapping, Optional, Set, Sequence,
                    Tuple)

from hook_tools import linters
from hook_tools import git_tools


def _unescape(s: str) -> str:
    '''Returns a version of the string without escaped entities.'''
    return s.replace('\\"', '"').replace('\\n', '\n')


class I18nLinter(linters.Linter):
    '''Runs i18n'''
    # pylint: disable=R0903

    # Paths
    _JS_TEMPLATES_PATH = 'frontend/www/js/omegaup'
    _TEMPLATES_PATH = 'frontend/templates'
    _BADGES_PATH = 'frontend/badges'

    # Colours
    _OKGREEN = git_tools.COLORS.OKGREEN
    _FAIL = git_tools.COLORS.FAIL
    _NORMAL = git_tools.COLORS.NORMAL
    _HEADER = git_tools.COLORS.HEADER
    _LANGS = ['en', 'es', 'pt']

    def __init__(self, options: Optional[linters.Options] = None):
        super().__init__()
        self.__options = options or {}

    @staticmethod
    def _generate_typescript(
            lang: str,
            strings: Mapping[str, Mapping[str, str]],
    ) -> str:
        '''Generates the TypeScript version of the i18n file.'''

        result = []
        result.append('// generated by stuff/i18n.py. DO NOT EDIT.')
        result.append('const translations: { [key: string]: string; } = {')
        for key in sorted(strings.keys()):
            result.append('  %s: %s,' %
                          (key, json.dumps(_unescape(strings[key][lang]))))
        result.append('};\n')
        result.append('export {translations as default};')
        return '\n'.join(result)

    @staticmethod
    def _generate_json(
            lang: str,
            strings: Mapping[str, Mapping[str, str]],
    ) -> str:
        '''Generates the JSON version of the i18n file.'''

        json_map: Dict[str, str] = {}
        for key in sorted(strings.keys()):
            json_map[key] = _unescape(strings[key][lang])
        return json.dumps(json_map, sort_keys=True, indent='\t')

    @staticmethod
    def _generate_sorted(
            lang: str,
            strings: Mapping[str, Mapping[str, str]],
    ) -> str:
        '''Generate the sorted version of the i18n file.'''

        result: List[str] = []
        for key in sorted(strings.keys()):
            result.append('%s = "%s"\n' %
                          (key, strings[key][lang].replace('"', r'\"')))
        return ''.join(result)

    @staticmethod
    def _pseudoloc(original: str) -> str:
        '''Converts the pseudoloc version of s.'''
        table = str.maketrans('elsot', '31507')
        tokens = re.split(r'(%\([a-zA-Z0-9_-]+\))', original)
        for i, token in enumerate(tokens):
            if token.startswith('%(') and token.endswith(')'):
                continue
            tokens[i] = token.translate(table)

        return '(%s)' % ''.join(tokens)

    def _add_badges_entries(
            self,
            contents_callback: linters.ContentsCallback,
    ) -> DefaultDict[str, DefaultDict[str, str]]:
        '''Adds badges name and description entries to .lang files'''
        aliases = [f.name for f in os.scandir(self._BADGES_PATH) if f.is_dir()]
        strings: DefaultDict[str,
                             DefaultDict[str, str]] = collections.defaultdict(
                                 lambda: collections.defaultdict(str))
        for alias in aliases:
            key_name = 'badge_%s_name' % alias
            key_desc = 'badge_%s_description' % alias
            filename = os.path.join(self._BADGES_PATH, alias,
                                    'localizations.json')
            contents = json.loads(contents_callback(filename).decode('utf-8'))
            for lang in self._LANGS:
                strings[key_name][lang] = contents[lang]['name']
                strings[key_desc][lang] = contents[lang]['description']
        return strings

    def _get_translated_strings(
            self,
            contents_callback: linters.ContentsCallback,
    ) -> Dict[str, Dict[str, str]]:
        strings: Dict[str, DefaultDict[str, str]] = {}
        languages: Set[str] = set()
        diagnostics: List[linters.Diagnostic] = []
        for lang in self._LANGS:
            filename = '%s/%s.lang' % (self._TEMPLATES_PATH, lang)
            languages.add(lang)
            for lineno, line in enumerate(
                    contents_callback(filename).split(b'\n')[:-1]):
                try:
                    row = line.decode('utf-8')
                    key, value = re.compile(r'\s+=\s+').split(row.strip(), 1)
                    if key not in strings:
                        strings[key] = collections.defaultdict(str)
                    match = re.compile(r'^"((?:[^"]|\\")*)"$').match(value)
                    if match is None:
                        raise Exception(f'Invalid line {row.strip()!r}')
                    strings[key][lang] = match.group(1).replace(r'\"', '"')
                except Exception as exc:  # pylint: disable=broad-except
                    diagnostics.append(
                        linters.Diagnostic(str(exc),
                                           filename=filename,
                                           lineno=lineno + 1,
                                           line=row.strip()))
        if diagnostics:
            raise linters.LinterException('Invalid i18n files',
                                          fixable=False,
                                          diagnostics=diagnostics)

        # Removing badges entries
        return {k: v for k, v in strings.items() if not k.startswith('badge_')}

    def _check_missing_entries(
            self,
            strings: Dict[str, Dict[str, str]],
            languages: Set[str],
    ) -> None:
        diagnostics: List[linters.Diagnostic] = []
        for key, values in strings.items():
            missing_languages = languages.difference(list(values.keys()))
            if missing_languages:
                for lang in missing_languages:
                    diagnostics.append(
                        linters.Diagnostic(f'Missing entry: {key!r}',
                                           filename=os.path.join(
                                               self._TEMPLATES_PATH,
                                               f'{lang}.lang')))
                continue

            if key == 'locale':
                values['pseudo'] = 'pseudo'
            else:
                values['pseudo'] = self._pseudoloc(values['en'])
        if diagnostics:
            raise linters.LinterException(
                'There are missing items in some files',
                diagnostics=diagnostics)

    @staticmethod
    def _generate_content_entry(
            new_contents: Dict[str, bytes],
            original_contents: Dict[str, bytes],
            path: str,
            new_content: str,
            contents_callback: linters.ContentsCallback,
    ) -> None:
        original_content = contents_callback(path)
        if original_content.decode('utf-8') != new_content:
            print('Entries in %s do not match the .lang file.' % path,
                  file=sys.stderr)
            new_contents[path] = new_content.encode('utf-8')
            original_contents[path] = original_content

    def _generate_new_contents(
            self,
            strings: Dict[str, Dict[str, str]],
            contents_callback: linters.ContentsCallback,
    ) -> Tuple[Mapping[str, bytes], Mapping[str, bytes]]:
        new_contents: Dict[str, bytes] = {}
        original_contents: Dict[str, bytes] = {}
        for language in self._LANGS + ['pseudo']:
            self._generate_content_entry(
                new_contents,
                original_contents,
                path='%s/%s.lang' % (self._TEMPLATES_PATH, language),
                new_content=self._generate_sorted(language, strings),
                contents_callback=contents_callback)
            self._generate_content_entry(
                new_contents,
                original_contents,
                path='%s/lang.%s.ts' % (self._JS_TEMPLATES_PATH, language),
                new_content=self._generate_typescript(language, strings),
                contents_callback=contents_callback)
            self._generate_content_entry(
                new_contents,
                original_contents,
                path='%s/lang.%s.json' % (self._JS_TEMPLATES_PATH, language),
                new_content=self._generate_json(language, strings),
                contents_callback=contents_callback)

        return new_contents, original_contents

    def run_all(
            self, filenames: Sequence[str],
            contents_callback: linters.ContentsCallback
    ) -> linters.MultipleResults:
        '''Runs the linter against a subset of files.'''
        # pylint: disable=no-self-use, unused-argument
        strings = self._get_translated_strings(contents_callback)
        strings.update(self._add_badges_entries(contents_callback))
        self._check_missing_entries(strings, set(self._LANGS))

        new_contents, original_contents = self._generate_new_contents(
            strings, contents_callback)

        return linters.MultipleResults(new_contents, original_contents,
                                       ['i18n'])

    @property
    def name(self) -> str:
        '''Gets the name of the linter.'''
        return 'i18n'


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
