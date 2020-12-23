from typing import List, Optional, cast

from anytree import NodeMixin, find
from galaxyls.services.tools.constants import (
    BOOLEAN,
    CONDITIONAL,
    FALSEVALUE,
    INPUTS,
    MIN,
    NAME,
    OPTION,
    PARAM,
    REPEAT,
    SECTION,
    SELECT,
    TRUEVALUE,
    TYPE,
    VALUE,
    WHEN,
)
from galaxyls.services.xml.nodes import XmlElement


class InputNode(NodeMixin):
    """Represents a logical input node in the tool wrapper file.

    Each node contains references to direct children classified by their type."""

    def __init__(self, name: str, element: Optional[XmlElement] = None, parent: NodeMixin = None):
        self.name: str = name
        self.element: Optional[XmlElement] = element
        self.parent = parent
        self.params: List[XmlElement] = []
        self.repeats: List[RepeatInputNode] = []
        self.sections: List[SectionInputNode] = []

    def __repr__(self) -> str:
        return self.name


class ConditionalInputNode(InputNode):
    """Represents a conditional input branch node in the tool wrapper file.

    The 'option_param' field contains the first select or boolean param and it's
    value is set to the 'option' field of one of the possible 'when' definitions.
    """

    def __init__(self, name: str, option: str, element: Optional[XmlElement] = None, parent: InputNode = None):
        super().__init__(name, element, parent)
        self.option_param: XmlElement = element.elements[0]
        self.option: str = option
        self.options: List[str] = self._get_options()

    def __repr__(self) -> str:
        return f"{self.name} - {self.option}"

    @property
    def is_first_option(self) -> bool:
        if self.options:
            return self.option == self.options[0]
        return True

    @property
    def is_last_option(self) -> bool:
        if self.options:
            return self.option == self.options[-1]
        return True

    def _get_options(self) -> List[str]:
        try:
            type_attr = self.option_param.get_attribute(TYPE)
            if type_attr == SELECT:
                options = self.option_param.get_children_with_name(OPTION)
                return list(filter(None, [option.get_attribute(VALUE) for option in options]))
            elif type_attr == BOOLEAN:
                options = []
                true_value = self.option_param.get_attribute(TRUEVALUE)
                if true_value:
                    options.append(true_value)
                false_value = self.option_param.get_attribute(FALSEVALUE)
                if false_value:
                    options.append(false_value)
                return options
            return []
        except BaseException:
            return []


class RepeatInputNode(InputNode):
    """Represents an input node that will be repeated 'min' times."""

    def __init__(self, name: str, min: int, element: Optional[XmlElement] = None):
        super().__init__(name, element, parent=None)
        self.min: int = min


class SectionInputNode(InputNode):
    """Represents a section input node which is used to group other nodes."""

    def __init__(self, name: str, element: Optional[XmlElement] = None):
        super().__init__(name, element, parent=None)


class GalaxyToolInputTree:
    """The branches of this tree contains all the inputs within a conditional path for a specific option."""

    def __init__(self, inputs: Optional[XmlElement] = None) -> None:
        self._root: InputNode = InputNode(INPUTS, inputs)
        if inputs:
            self._build_input_tree(inputs, self._root)

    @property
    def leaves(self) -> List[InputNode]:
        """The leaves of the tree contain all the final elements of the conditional branches."""
        return list(self._root.leaves)

    def _build_input_tree(self, inputs: XmlElement, parent: InputNode) -> None:
        """Given the XML element containing the inputs of the tool, this method recursively builds
        an expanded input tree.

        Args:
            inputs (XmlElement): The XML element corresponding to the inputs.
            parent (InputNode): The node that will hold all the inputs.
        """
        parent.params = inputs.get_children_with_name(PARAM)

        conditionals = inputs.get_children_with_name(CONDITIONAL)
        for conditional in conditionals:
            self._build_conditional_input_tree(conditional, parent)

        repeats = inputs.get_children_with_name(REPEAT)
        for repeat in repeats:
            repeat_node = self._build_repeat_input_tree(repeat)
            if repeat_node:
                parent.repeats.append(repeat_node)

        sections = inputs.get_children_with_name(SECTION)
        for section in sections:
            section_node = self._build_section_input_tree(section)
            if section_node:
                parent.sections.append(section_node)

    def _build_conditional_input_tree(self, conditional: XmlElement, parent: InputNode) -> None:
        """Populates the 'parent' node with a ConditionalInputNode for each of the declared options
        in the given 'conditional' XmlElement.

        Args:
            conditional (XmlElement): The XML element (conditional tag).
            parent (InputNode): The InputNode that will hold the conditional branches and it's elements.
        """
        param = conditional.elements[0]  # first child must be select or boolean
        if param.get_attribute(TYPE) == SELECT:
            options = param.get_children_with_name(OPTION)
            for option in options:
                option_value = option.get_attribute(VALUE)
                self._build_conditional_option_branch(conditional, parent, option_value)
        elif param.get_attribute(TYPE) == BOOLEAN:
            true_value = param.get_attribute(TRUEVALUE)
            if true_value:
                self._build_conditional_option_branch(conditional, parent, true_value)
            false_value = param.get_attribute(FALSEVALUE)
            if false_value:
                self._build_conditional_option_branch(conditional, parent, false_value)

    def _build_conditional_option_branch(
        self, conditional: XmlElement, parent: InputNode, option_value: Optional[str] = None
    ) -> None:
        """Builds a conditional branch in the input tree with the given 'option_value'.

        Args:
            conditional (XmlElement): The <conditional> XML element.
            parent (InputNode): The input node that will contain this branch.
            option_value (str): The value of the option selected in this conditional branch.
        """
        name = conditional.get_attribute(NAME)
        if name and option_value:
            conditional_node = ConditionalInputNode(name, option_value, element=conditional, parent=parent)
            when = find(conditional, filter_=lambda el: el.name == WHEN and el.get_attribute(VALUE) == option_value)
            when = cast(XmlElement, when)
            if when:
                self._build_input_tree(when, conditional_node)

    def _build_repeat_input_tree(self, repeat: XmlElement) -> Optional[RepeatInputNode]:
        """Builds and returns a RepeatInputNode from a 'repeat' XML tag with the minimum number
        of repetitions defined.

        Args:
            repeat (XmlElement): The XML repeat tag.

        Returns:
            Optional[RepeatInputNode]: The resulting RepeatInputNode with it's own input children.
        """
        name = repeat.get_attribute(NAME)
        if name:
            min = 1
            min_attr = repeat.get_attribute(MIN)
            if min_attr and min_attr.isdigit:
                min = int(min_attr)
            repeat_node = RepeatInputNode(name, min, repeat)
            self._build_input_tree(repeat, repeat_node)
            return repeat_node
        return None

    def _build_section_input_tree(self, section: XmlElement) -> Optional[SectionInputNode]:
        """Builds and returns a SectionInputNode from a 'section' XML tag.

        Args:
            section (XmlElement): The XML section tag.

        Returns:
            Optional[SectionInputNode]: The resulting SectionInputNode with it's own input children.
        """
        name = section.get_attribute(NAME)
        if name:
            section_node = SectionInputNode(name, section)
            self._build_input_tree(section, section_node)
            return section_node
        return None
