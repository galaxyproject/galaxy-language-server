from typing import List, cast
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
from pygls.lsp.types import Diagnostic, Range, DiagnosticSeverity


class GalaxyToolLinter(ToolLinter):
    diagnostics_source = "Galaxy Tool Linter"

    def lint_document(self, xml_document: XmlDocument) -> List[Diagnostic]:
        """ """
        result: List[Diagnostic] = []
        if xml_document.is_macros_file:
            return result
        xml_tree, _ = xml_macros.load_with_references(xml_document.document.path)
        tool_source = get_tool_source(xml_tree=xml_tree)
        lint_context = LintContext(level=LintLevel.SILENT, lint_message_class=XMLLintMessageXPath)
        context = lint_tool_source_with(lint_context, tool_source)
        result.extend(
            [
                self._to_diagnostic(lint_message, xml_tree, xml_document, DiagnosticSeverity.Error)
                for lint_message in context.error_messages
            ]
        )
        result.extend(
            [
                self._to_diagnostic(lint_message, xml_tree, xml_document, DiagnosticSeverity.Warning)
                for lint_message in context.warn_messages
            ]
        )
        return result

    def _to_diagnostic(
        self,
        lint_message: XMLLintMessageXPath,
        xml_tree: etree._ElementTree,
        xml_document: XmlDocument,
        level: DiagnosticSeverity,
    ) -> Diagnostic:
        range = self._get_range_from_xpath(lint_message.xpath, xml_tree, xml_document)
        result = Diagnostic(
            range=range,
            message=lint_message.message,
            source=self.diagnostics_source,
            severity=level,
        )
        return result

    def _get_range_from_xpath(self, xpath: str, xml_tree: etree._ElementTree, xml_document: XmlDocument) -> Range:
        result = None
        found = cast(list, xml_tree.xpath(xpath))[0]
        if found is not None:
            result = xml_document.get_element_name_range_at_line(found.tag, found.sourceline - 1)
        return result or xml_document.get_default_range()
