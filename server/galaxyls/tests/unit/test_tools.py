import pytest
from lsprotocol.types import (
    Position,
    Range,
)

from galaxyls.services.tools.document import GalaxyToolXmlDocument
from galaxyls.services.tools.generators.command import GalaxyToolCommandSnippetGenerator
from galaxyls.services.tools.generators.tests import GalaxyToolTestSnippetGenerator, GalaxyToolTestUpdater
from galaxyls.tests.unit.sample_data import TEST_TOOL_WITH_INPUTS_DOCUMENT
from galaxyls.tests.unit.utils import TestUtils
from galaxyls.types import ReplaceTextRangeResult, WorkspaceEditResult


class TestGalaxyToolXmlDocumentClass:
    def test_init_sets_properties(self) -> None:
        document = TestUtils.to_document("<tool></tool>")
        tool = GalaxyToolXmlDocument(document)

        assert not tool.xml_document.is_empty

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("", False),
            ("<macros>", False),
            ("<macros></macros>", False),
            ("<tool>", True),
            ("<tool></tool>", True),
        ],
    )
    def test_is_valid(self, source: str, expected: bool) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)

        assert tool.is_valid == expected

    def test_find_tests_section_without_section_returns_none(self) -> None:
        document = TestUtils.to_document("<tool></tool>")
        tool = GalaxyToolXmlDocument(document)

        actual = tool.find_element("notexistent")

        assert actual is None

    def test_find_tests_section_returns_expected(self) -> None:
        document = TestUtils.to_document("<tool><tests></tests></tool>")
        tool = GalaxyToolXmlDocument(document)

        actual = tool.find_element("tests")

        assert actual
        assert actual.name == "tests"

    def test_get_element_content_range_of_unknown_element_returns_none(self) -> None:
        document = TestUtils.to_document("<tool><tests></tests></tool>")
        tool = GalaxyToolXmlDocument(document)
        node = tool.find_element("unknown")

        actual = tool.get_content_range(node)

        assert actual is None

    @pytest.mark.parametrize(
        "source, element, expected",
        [
            ("<tool><tests/></tool>", "tests", None),
            (
                "<tool><tests></tests></tool>",
                "tests",
                Range(start=Position(line=0, character=13), end=Position(line=0, character=13)),
            ),
            (
                "<tool><tests>\n</tests></tool>",
                "tests",
                Range(start=Position(line=0, character=13), end=Position(line=1, character=0)),
            ),
            (
                "<tool>\n<tests>\n   \n</tests>\n</tool>",
                "tests",
                Range(start=Position(line=1, character=7), end=Position(line=3, character=0)),
            ),
            (
                "<tool>\n<tests>\n<test/></tests></tool>",
                "tests",
                Range(start=Position(line=1, character=7), end=Position(line=2, character=7)),
            ),
        ],
    )
    def test_get_element_content_range_of_element_returns_expected(self, source: str, element: str, expected: Range) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)
        node = tool.find_element(element)

        actual = tool.get_content_range(node)

        assert actual == expected

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("", False),
            ("<macros>", False),
            ("<macros></macros>", False),
            ("<tool></tool>", False),
            ("<tool><macros></macros></tool>", False),
            ("<tool><expand/></tool>", True),
            ("<tool><expand></tool>", True),
            ("<tool><expand></expand></tool>", True),
            ("<tool><expand/><expand/></tool>", True),
            ("<tool><token/></tool>", True),
            ("<tool><import/></tool>", True),
            ("<tool><xml/></tool>", True),
            ("<tool><macro/></tool>", True),
        ],
    )
    def test_uses_macros_returns_expected(self, source: str, expected: bool) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)

        assert tool.uses_macros == expected

    def test_analyze_inputs_returns_expected_number_of_leaves(self) -> None:
        tool = GalaxyToolXmlDocument(TEST_TOOL_WITH_INPUTS_DOCUMENT)
        result = tool.analyze_inputs()

        assert len(result.leaves) == 3

    @pytest.mark.parametrize(
        "source, element_name, expected_position",
        [
            ("<tool></tool>", "tool", Position(line=0, character=0)),
            ("<tool><description/><inputs></tool>", "description", Position(line=0, character=6)),
            ("<tool><description/><inputs></tool>", "inputs", Position(line=0, character=20)),
            ("<tool><macros><import></macros></tool>", "import", Position(line=0, character=14)),
            ("<tool>\n<macros>\n<import></macros></tool>", "import", Position(line=2, character=0)),
        ],
    )
    def test_get_position_before_element_returns_expected_position(
        self, source: str, element_name: str, expected_position: Position
    ) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)
        element = tool.find_element(element_name, maxlevel=4)

        assert element is not None
        actual_position = tool.get_position_before(element)
        assert actual_position == expected_position

    @pytest.mark.parametrize(
        "source, element_name, expected_position",
        [
            ("<tool></tool>", "tool", Position(line=0, character=13)),
            ("<tool><description/><inputs></tool>", "description", Position(line=0, character=20)),
            ("<tool><description/>\n<inputs></tool>", "description", Position(line=0, character=20)),
            ("<tool>\n<description/>\n<inputs></tool>", "description", Position(line=1, character=14)),
            ("<tool><description/><inputs></tool>", "inputs", Position(line=0, character=28)),
            ("<tool><macros><import></macros></tool>", "import", Position(line=0, character=22)),
            ("<tool>\n<macros>\n<import></macros></tool>", "import", Position(line=2, character=8)),
        ],
    )
    def test_get_position_after_element_returns_expected_position(
        self, source: str, element_name: str, expected_position: Position
    ) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)
        element = tool.find_element(element_name, maxlevel=4)

        assert element is not None
        actual_position = tool.get_position_after(element)
        assert actual_position == expected_position


class TestGalaxyToolTestSnippetGeneratorClass:
    @pytest.mark.parametrize(
        "tool_file, expected_snippet_file",
        [
            ("simple_conditional_01.xml", "simple_conditional_01_test.xml"),
            ("simple_conditional_02.xml", "simple_conditional_02_test.xml"),
            ("simple_params_01.xml", "simple_params_01_test.xml"),
            ("simple_repeat_01.xml", "simple_repeat_01_test.xml"),
            ("simple_section_01.xml", "simple_section_01_test.xml"),
            ("simple_output_01.xml", "simple_output_01_test.xml"),
            ("simple_output_02.xml", "simple_output_02_test.xml"),
            ("complex_inputs_01.xml", "complex_inputs_01_test.xml"),
            ("nested_conditional_bug_01.xml", "nested_conditional_bug_01_test.xml"),
        ],
    )
    def test_build_snippet_returns_expected_result(self, tool_file: str, expected_snippet_file: str) -> None:
        document = TestUtils.get_test_document_from_file(tool_file)
        expected_snippet = TestUtils.get_test_file_contents(expected_snippet_file)
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolTestSnippetGenerator(tool)

        actual_snippet, is_error = generator._build_snippet()
        print(actual_snippet)
        assert actual_snippet == expected_snippet
        assert not is_error

    @pytest.mark.parametrize(
        "source, expected_position",
        [
            ("<tool></tool>", Position(line=0, character=6)),
            ("<tool><description/><inputs></tool>", Position(line=0, character=28)),
            ("<tool><tests></tests></tool>", Position(line=0, character=13)),
            ("<tool><tests/></tool>", Range(start=Position(line=0, character=6), end=Position(line=0, character=14))),
        ],
    )
    def test_find_snippet_position_returns_expected_result(self, source: str, expected_position: Position) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolTestSnippetGenerator(tool)

        actual_position = generator._find_snippet_insert_position()

        assert actual_position == expected_position

    def test_generate_snippet_without_tests_section_returns_tests_tag(self) -> None:
        document = TestUtils.to_document("<tool></tool>")
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolTestSnippetGenerator(tool)

        result = generator.generate_snippet()

        assert "<tests>" in result.snippet

    def test_generate_snippet_with_tests_section_returns_snippet_only(self) -> None:
        document = TestUtils.to_document("<tool><tests></tests></tool>")
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolTestSnippetGenerator(tool)

        result = generator.generate_snippet()

        assert "<tests>" not in result.snippet


class TestGalaxyToolCommandSnippetGeneratorClass:
    @pytest.mark.parametrize(
        "tool_file, expected_snippet_file",
        [
            ("simple_conditional_01.xml", "simple_conditional_01_command.xml"),
            ("simple_conditional_02.xml", "simple_conditional_02_command.xml"),
            ("simple_params_01.xml", "simple_params_01_command.xml"),
            ("simple_repeat_01.xml", "simple_repeat_01_command.xml"),
            ("simple_section_01.xml", "simple_section_01_command.xml"),
            ("simple_output_01.xml", "simple_output_01_command.xml"),
            ("simple_output_02.xml", "simple_output_02_command.xml"),
            ("complex_inputs_01.xml", "complex_inputs_01_command.xml"),
            ("nested_conditional_bug_01.xml", "nested_conditional_bug_01_command.xml"),
        ],
    )
    def test_build_snippet_returns_expected_result(self, tool_file: str, expected_snippet_file: str) -> None:
        document = TestUtils.get_test_document_from_file(tool_file)
        expected_snippet = TestUtils.get_test_file_contents(expected_snippet_file)
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolCommandSnippetGenerator(tool)

        actual_snippet, is_error = generator._build_snippet()
        print(actual_snippet)
        assert actual_snippet == expected_snippet
        assert not is_error

    @pytest.mark.parametrize(
        "source, expected_position",
        [
            ("<tool></tool>", Position(line=0, character=6)),
            ("<tool><description/><inputs></tool>", Position(line=0, character=20)),
            ("<tool><command></command></tool>", Position(line=0, character=15)),
            ("<tool><command><![CDATA[]]></command></tool>", Position(line=0, character=24)),
            ("<tool><command/></tool>", Range(start=Position(line=0, character=6), end=Position(line=0, character=16))),
        ],
    )
    def test_find_snippet_position_returns_expected_result(self, source: str, expected_position: Position) -> None:
        document = TestUtils.to_document(source)
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolCommandSnippetGenerator(tool)

        actual_position = generator._find_snippet_insert_position()

        assert actual_position == expected_position

    def test_generate_snippet_without_command_returns_command_tag_with_cdata(self) -> None:
        document = TestUtils.to_document("<tool></tool>")
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolCommandSnippetGenerator(tool)

        result = generator.generate_snippet()

        assert "<command" in result.snippet
        assert "<![CDATA[" in result.snippet

    def test_generate_snippet_with_command_no_cdata_returns_cdata(self) -> None:
        document = TestUtils.to_document("<tool><command></command></tool>")
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolCommandSnippetGenerator(tool)

        result = generator.generate_snippet()

        assert "<command" not in result.snippet
        assert "<![CDATA[" in result.snippet

    def test_generate_snippet_with_command_with_cdata_returns_snippet_only(self) -> None:
        document = TestUtils.to_document("<tool><command><![CDATA[]]></command></tool>")
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolCommandSnippetGenerator(tool)

        result = generator.generate_snippet()

        assert "<command" not in result.snippet
        assert "<![CDATA[" not in result.snippet


class TestGalaxyToolTestUpdaterClass:
    @pytest.mark.parametrize(
        "tool_file, expected_workspace_edit",
        [
            (
                "update_profile_simple_01.xml",
                WorkspaceEditResult(
                    edits=[
                        ReplaceTextRangeResult(
                            replace_range=Range(
                                start=Position(line=29, character=12),
                                end=Position(line=29, character=48),
                            ),
                            text='<conditional name="c1">\n  <param name="c1_action" value="a1"/>\n  <param name="c1_a1_p1" value="A 1"/>\n</conditional>\n',
                        ),
                        ReplaceTextRangeResult(
                            replace_range=Range(
                                start=Position(line=31, character=12),
                                end=Position(line=31, character=45),
                            ),
                            text='<repeat name="rep1">\n  <param name="rep1_p1" value="r"/>\n</repeat>\n',
                        ),
                        ReplaceTextRangeResult(
                            replace_range=Range(
                                start=Position(line=32, character=12),
                                end=Position(line=32, character=46),
                            ),
                            text='<section name="int">\n  <param name="int_test" value="1"/>\n</section>\n',
                        ),
                        ReplaceTextRangeResult(
                            replace_range=Range(
                                start=Position(line=30, character=12),
                                end=Position(line=30, character=48),
                            ),
                            text="",
                        ),
                        ReplaceTextRangeResult(
                            replace_range=Range(
                                start=Position(line=40, character=12),
                                end=Position(line=40, character=48),
                            ),
                            text='<conditional name="c1">\n  <param name="c1_action" value="a2"/>\n  <param name="c1_a2_p1" value="A 2"/>\n</conditional>\n',
                        ),
                        ReplaceTextRangeResult(
                            replace_range=Range(
                                start=Position(line=41, character=12),
                                end=Position(line=41, character=48),
                            ),
                            text="",
                        ),
                    ],
                ),
            ),
        ],
    )
    def test_build_snippet_returns_expected_result(self, tool_file: str, expected_workspace_edit: WorkspaceEditResult) -> None:
        document = TestUtils.get_test_document_from_file(tool_file)
        tool = GalaxyToolXmlDocument(document)
        generator = GalaxyToolTestUpdater(tool)

        actual_workspace_edit = generator.generate_workspace_edit()

        assert actual_workspace_edit.error_message == expected_workspace_edit.error_message
        for i, edit in enumerate(actual_workspace_edit.edits):
            assert edit.replace_range == expected_workspace_edit.edits[i].replace_range
            assert edit.text == expected_workspace_edit.edits[i].text
