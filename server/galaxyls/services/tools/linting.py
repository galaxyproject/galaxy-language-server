from typing import List
from lxml import etree

from galaxy.tool_util.lint import (
    lint_tool_source_with,
    LintContext,
    LintLevel,
    XMLLintMessageXPath,
)
from galaxy.tool_util.parser import get_tool_source
from galaxy.util import xml_macros
from galaxyls.services.tools.common import ToolLinter
from galaxyls.services.xml.document import XmlDocument
from pygls.lsp.types import Diagnostic, Range, Position, DiagnosticSeverity


class GalaxyToolLinter(ToolLinter):
    def lint_document(self, xml_document: XmlDocument) -> List[Diagnostic]:
        """ """
        result = []
        xml_tree, _ = xml_macros.load_with_references(xml_document.document.path)
        try:
            tool_source = get_tool_source(xml_tree=xml_tree)
            lint_context = LintContext(level=LintLevel.SILENT, lint_message_class=XMLLintMessageXPath)
            context = lint_tool_source_with(lint_context, tool_source)
            result.extend(
                [
                    self._to_diagnostic(lint_message, xml_tree, DiagnosticSeverity.Error)
                    for lint_message in context.error_messages
                ]
            )
            result.extend(
                [
                    self._to_diagnostic(lint_message, xml_tree, DiagnosticSeverity.Warning)
                    for lint_message in context.warn_messages
                ]
            )
        except BaseException as e:
            print(e)
        return result

    def _to_diagnostic(
        self,
        lint_message: XMLLintMessageXPath,
        xml_tree: etree._ElementTree,
        level: DiagnosticSeverity,
    ) -> List[Diagnostic]:
        range = self._get_range_from_xpath(lint_message.xpath, xml_tree)
        result = Diagnostic(
            range=range,
            message=lint_message.message,
            source="Galaxy Tool Linter",
            severity=level,
        )
        return result

    def _get_range_from_xpath(self, xpath: str, xml_tree: etree._ElementTree) -> Range:
        result = None
        try:
            found = xml_tree.xpath(xpath)[0]
            if found:
                result = Range(
                    start=Position(line=found.sourceline - 1, character=0),
                    end=Position(line=found.sourceline - 1, character=0),
                )
        except BaseException as e:
            print(e)
        return result or Range(
            start=Position(line=0, character=0),
            end=Position(line=0, character=0),
        )
