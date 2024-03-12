"""Warning utility functions."""
from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Protocol, TextIO, TypeAlias

if TYPE_CHECKING:
    from types import TracebackType

    WarningFilter: TypeAlias = tuple[str, str | None, type[Warning], str | None, int]

    class ShowWarning(Protocol):  # noqa: D101
        def __call__(  # noqa: PLR0913, D102
            self,
            message: Warning | str,
            category: type[Warning],
            filename: str,
            lineno: int,
            file: TextIO | None = None,
            line: str | None = None,
        ) -> None:
            ...


@dataclass
class extract_warnings:  # noqa: N801
    """Record warnings matching certain criteria."""

    message: str = ""
    category: type[Warning] = Warning

    old_showwarning: ShowWarning = field(init=False, repr=False, default=warnings.showwarning)
    old_filters: tuple[WarningFilter, ...] = field(init=False, repr=False, default=())
    messages: list[warnings.WarningMessage] = field(init=False, repr=False, default_factory=list)

    def handle_warning(  # noqa: PLR0913
        self,
        message: Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: TextIO | None = None,
        line: str | None = None,
    ) -> None:
        """Record the warning if it matches the criteria, otherwise show it."""
        if re.match(self.message, str(message)) and issubclass(category, self.category):
            self.messages.append(warnings.WarningMessage(message, category, filename, lineno, file, line))
        else:
            self.old_showwarning(message, category, filename, lineno, file, line)

    def __enter__(self) -> list[warnings.WarningMessage]:
        """Set up the warning filter and showwarning function. Return the list of to-be-recorded warnings."""
        self.old_showwarning = warnings.showwarning
        self.old_filters = tuple(warnings.filters)
        self.messages.clear()
        warnings.filterwarnings("always", self.message, self.category)
        warnings.showwarning = self.handle_warning
        return self.messages

    def __exit__(
        self,
        type: type[BaseException] | None,  # noqa: A002
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        """Restore the warning filter and showwarning function."""
        warnings.filters = list(self.old_filters)
        warnings.showwarning = self.old_showwarning
        if (fm := getattr(warnings, "_filters_mutated", None)) and callable(fm):
            fm()
        return False  # Do not suppress exception
