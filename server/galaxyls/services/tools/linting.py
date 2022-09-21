from typing import List

from galaxy.tool_util.lint import (
    lint_xml_with,
    LintContext,
    LintLevel,
    XMLLintMessageXPath,
)
from pygls.lsp.types import (
    Diagnostic,
    DiagnosticSeverity,
)

from galaxyls.services.tools.common import ToolLinter
from galaxyls.services.xml.document import XmlDocument


class GalaxyToolLinter(ToolLinter):
    diagnostics_source = "Galaxy Tool Linter"

    def lint_document(self, xml_document: XmlDocument) -> List[Diagnostic]:
        """ """
        result: List[Diagnostic] = []
        xml_tree = xml_document.xml_tree_expanded
        if not xml_document.is_tool_file or xml_tree is None:
            return result
        lint_context = LintContext(level=LintLevel.SILENT, lint_message_class=XMLLintMessageXPath)
        context = lint_xml_with(lint_context, xml_tree)
        result.extend(
            [
                self._to_diagnostic(lint_message, xml_document, DiagnosticSeverity.Error)
                for lint_message in context.error_messages
            ]
        )
        result.extend(
            [
                self._to_diagnostic(lint_message, xml_document, DiagnosticSeverity.Warning)
                for lint_message in context.warn_messages
            ]
        )
        return result

    def _to_diagnostic(
        self,
        lint_message: XMLLintMessageXPath,
        xml_document: XmlDocument,
        level: DiagnosticSeverity,
    ) -> Diagnostic:
        range = xml_document.get_element_range_from_xpath_or_default(lint_message.xpath)
        result = Diagnostic(
            range=range,
            message=lint_message.message,
            source=self.diagnostics_source,
            severity=level,
        )
        return result
