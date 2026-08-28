from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.comments.schemas import (
    CommentCreate,
    CommentListQuery,
    CommentPage,
)


def test_comment_valid_values_is_created() -> None:
    # Arrange + Act
    comment = CommentCreate(
        content="test-comment",
    )

    # Assert
    assert comment.content == "test-comment"


def test_leading_and_trailing_spaces_are_normalized() -> None:
    # Arrange + Act
    comment = CommentCreate(
        content="  test-comment      ",
    )

    # Assert
    assert comment.content == "test-comment"


@pytest.mark.parametrize(
    "content",
    [
        "",
        "    ",
        "a" * 5001,
    ],
)
def test_invalid_content_is_rejected(content: str) -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        CommentCreate(
            content=content,
        )


def test_extra_field_for_comment_is_rejected() -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        CommentCreate.model_validate(
            {
                "author_id": str(uuid4()),
                "content": "test-content",
            }
        )


def test_comment_list_query_with_default_values_succeeds() -> None:
    # Arrange
    comment_list = CommentListQuery()

    assert comment_list.page == 1
    assert comment_list.page_size == 20
    assert comment_list.offset == 0


def test_comment_list_query_with_valid_values_succeeds() -> None:
    # Arrange
    comment_list = CommentListQuery(
        page=3,
        page_size=10,
    )

    assert comment_list.page == 3
    assert comment_list.page_size == 10
    assert comment_list.offset == 20


@pytest.mark.parametrize(
    ("page", "page_size"),
    [
        (0, 20),
        (-1, 20),
        (1, 0),
        (1, 101),
    ],
)
def test_comment_list_query_with_invalid_pagination(
    page: int,
    page_size: int,
) -> None:
    # Arrange + Act + Assert
    with pytest.raises(ValidationError):
        CommentListQuery(
            page=page,
            page_size=page_size,
        )


def test_comment_page_with_default_values() -> None:
    # Arrange + Act
    comment_page = CommentPage(
        items=[],
        page=1,
        page_size=4,
        total=0,
    )

    # Assert
    assert comment_page.total == 0
    assert comment_page.pages == 0


def test_comment_page_with_valid_values() -> None:
    # Arrange + Act
    comment_page = CommentPage(
        items=[],
        page=1,
        total=21,
        page_size=20,
    )

    # Assert
    assert comment_page.total == 21
    assert comment_page.page_size == 20
    assert comment_page.pages == 2
