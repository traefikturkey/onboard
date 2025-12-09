"""API routes for bookmark management."""

import logging
from typing import Any

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from app.models.bookmark_api import (
    BookmarkItem,
    CreateSectionRequest,
    ErrorResponse,
    FolderItem,
    ImportBookmarksRequest,
    MoveBookmarkRequest,
    ReorderRequest,
    SectionBookmarkItem,
    SuccessResponse,
    UpdateSectionRequest,
)
from app.services.bookmark_manager import (
    BookmarkManager,
    BookmarkNotFoundError,
    InvalidIndexError,
    SectionNotFoundError,
)

logger = logging.getLogger(__name__)


def create_bookmarks_blueprint(bookmark_manager=None):
    """
    Create bookmarks API blueprint with optional injected bookmark manager.

    Args:
        bookmark_manager: Optional BookmarkManager instance. If not provided,
                         uses the one from current_app.extensions.

    Returns:
        Configured Blueprint instance
    """
    bookmarks_bp = Blueprint("bookmarks_api", __name__, url_prefix="/api/bookmarks")

    def get_manager():
        """Get the bookmark manager from injection or current_app."""
        if bookmark_manager is not None:
            return bookmark_manager
        # Try to get from app extensions (factory pattern)
        mgr = current_app.extensions.get("onboard_bookmark_manager")
        if mgr is not None:
            return mgr
        # Fallback: create a new one (backward compatibility)
        return BookmarkManager()

    def handle_error(e: Exception, status_code: int = 400) -> tuple[dict[str, Any], int]:
        """Handle exceptions and return error response."""
        logger.error(f"API error: {e}")
        error_response = ErrorResponse(error=type(e).__name__, details=str(e))
        return error_response.model_dump(), status_code

    # Bar Bookmark Routes

    @bookmarks_bp.route("/bar", methods=["GET"])
    def get_bar_bookmarks():
        """Get all bar bookmarks."""
        try:
            bookmarks = get_manager().get_bar_bookmarks()
            return jsonify(SuccessResponse(data=bookmarks).model_dump())
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/bar", methods=["POST"])
    def add_bar_bookmark():
        """Add a bookmark to the bar."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                if "contents" in data:
                    validated = FolderItem(**data)
                else:
                    validated = BookmarkItem(**data)
                bookmark_data = validated.model_dump(exclude_none=True)
            except ValidationError as ve:
                return handle_error(ve, 400)

            result = get_manager().add_bar_bookmark(bookmark_data)
            return (
                jsonify(
                    SuccessResponse(
                        message="Bookmark added successfully", data=result
                    ).model_dump()
                ),
                201,
            )
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/bar/<int:index>", methods=["GET"])
    def get_bar_bookmark(index: int):
        """Get a specific bar bookmark by index."""
        try:
            bookmark = get_manager().get_bar_bookmark(index)
            return jsonify(SuccessResponse(data=bookmark).model_dump())
        except InvalidIndexError as e:
            return handle_error(e, 404)
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/bar/<int:index>", methods=["PUT"])
    def update_bar_bookmark(index: int):
        """Update a bar bookmark at a specific index."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                if "contents" in data:
                    validated = FolderItem(**data)
                else:
                    validated = BookmarkItem(**data)
                bookmark_data = validated.model_dump(exclude_none=True)
            except ValidationError as ve:
                return handle_error(ve, 400)

            result = get_manager().update_bar_bookmark(index, bookmark_data)
            return jsonify(
                SuccessResponse(
                    message="Bookmark updated successfully", data=result
                ).model_dump()
            )
        except InvalidIndexError as e:
            return handle_error(e, 404)
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/bar/<int:index>", methods=["DELETE"])
    def delete_bar_bookmark(index: int):
        """Delete a bar bookmark at a specific index."""
        try:
            get_manager().delete_bar_bookmark(index)
            return jsonify(
                SuccessResponse(message="Bookmark deleted successfully").model_dump()
            )
        except InvalidIndexError as e:
            return handle_error(e, 404)
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/bar/reorder", methods=["POST"])
    def reorder_bar_bookmarks():
        """Reorder bar bookmarks."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = ReorderRequest(**data)
            except ValidationError as ve:
                return handle_error(ve, 400)

            result = get_manager().reorder_bar_bookmarks(validated.indices)
            return jsonify(
                SuccessResponse(
                    message="Bookmarks reordered successfully", data=result
                ).model_dump()
            )
        except (ValueError, InvalidIndexError) as e:
            return handle_error(e, 400)
        except Exception as e:
            return handle_error(e, 500)

    # Section Routes

    @bookmarks_bp.route("/sections", methods=["GET"])
    def get_all_sections():
        """Get all sections."""
        try:
            sections = get_manager().get_all_sections()
            return jsonify(SuccessResponse(data=sections).model_dump())
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/sections", methods=["POST"])
    def create_section():
        """Create a new section."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = CreateSectionRequest(**data)
            except ValidationError as ve:
                return handle_error(ve, 400)

            result = get_manager().create_section(
                validated.section_id, validated.displayName
            )
            return (
                jsonify(
                    SuccessResponse(
                        message="Section created successfully",
                        data={"section_id": validated.section_id, **result},
                    ).model_dump()
                ),
                201,
            )
        except ValueError as e:
            return handle_error(e, 409)
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/sections/<section_id>", methods=["GET"])
    def get_section(section_id: str):
        """Get a specific section by ID."""
        try:
            section = get_manager().get_section(section_id)
            return jsonify(SuccessResponse(data=section).model_dump())
        except SectionNotFoundError as e:
            return handle_error(e, 404)
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/sections/<section_id>", methods=["PUT"])
    def update_section(section_id: str):
        """Update a section's metadata."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = UpdateSectionRequest(**data)
            except ValidationError as ve:
                return handle_error(ve, 400)

            result = get_manager().update_section(section_id, validated.model_dump())
            return jsonify(
                SuccessResponse(
                    message="Section updated successfully", data=result
                ).model_dump()
            )
        except SectionNotFoundError as e:
            return handle_error(e, 404)
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/sections/<section_id>", methods=["DELETE"])
    def delete_section(section_id: str):
        """Delete a section."""
        try:
            get_manager().delete_section(section_id)
            return jsonify(
                SuccessResponse(message="Section deleted successfully").model_dump()
            )
        except SectionNotFoundError as e:
            return handle_error(e, 404)
        except Exception as e:
            return handle_error(e, 500)

    # Section Bookmark Routes

    @bookmarks_bp.route("/sections/<section_id>/bookmarks", methods=["GET"])
    def get_section_bookmarks(section_id: str):
        """Get all bookmarks in a section."""
        try:
            bookmarks = get_manager().get_section_bookmarks(section_id)
            return jsonify(SuccessResponse(data=bookmarks).model_dump())
        except SectionNotFoundError as e:
            return handle_error(e, 404)
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/sections/<section_id>/bookmarks", methods=["POST"])
    def add_section_bookmark(section_id: str):
        """Add a bookmark to a section."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = SectionBookmarkItem(**data)
                bookmark_data = validated.model_dump()
            except ValidationError as ve:
                return handle_error(ve, 400)

            result = get_manager().add_section_bookmark(section_id, bookmark_data)
            return (
                jsonify(
                    SuccessResponse(
                        message="Bookmark added to section successfully", data=result
                    ).model_dump()
                ),
                201,
            )
        except SectionNotFoundError as e:
            return handle_error(e, 404)
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/sections/<section_id>/bookmarks/<int:index>", methods=["PUT"])
    def update_section_bookmark(section_id: str, index: int):
        """Update a bookmark in a section."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = SectionBookmarkItem(**data)
                bookmark_data = validated.model_dump()
            except ValidationError as ve:
                return handle_error(ve, 400)

            result = get_manager().update_section_bookmark(
                section_id, index, bookmark_data
            )
            return jsonify(
                SuccessResponse(
                    message="Bookmark updated successfully", data=result
                ).model_dump()
            )
        except SectionNotFoundError as e:
            return handle_error(e, 404)
        except InvalidIndexError as e:
            return handle_error(e, 404)
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/sections/<section_id>/bookmarks/<int:index>", methods=["DELETE"])
    def delete_section_bookmark(section_id: str, index: int):
        """Delete a bookmark from a section."""
        try:
            get_manager().delete_section_bookmark(section_id, index)
            return jsonify(
                SuccessResponse(message="Bookmark deleted successfully").model_dump()
            )
        except SectionNotFoundError as e:
            return handle_error(e, 404)
        except InvalidIndexError as e:
            return handle_error(e, 404)
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/sections/<section_id>/bookmarks/reorder", methods=["POST"])
    def reorder_section_bookmarks(section_id: str):
        """Reorder bookmarks in a section."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = ReorderRequest(**data)
            except ValidationError as ve:
                return handle_error(ve, 400)

            result = get_manager().reorder_section_bookmarks(
                section_id, validated.indices
            )
            return jsonify(
                SuccessResponse(
                    message="Bookmarks reordered successfully", data=result
                ).model_dump()
            )
        except SectionNotFoundError as e:
            return handle_error(e, 404)
        except (ValueError, InvalidIndexError) as e:
            return handle_error(e, 400)
        except Exception as e:
            return handle_error(e, 500)

    # Advanced Operation Routes

    @bookmarks_bp.route("/move", methods=["POST"])
    def move_bookmark():
        """Move a bookmark between bar and sections."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = MoveBookmarkRequest(**data)
            except ValidationError as ve:
                return handle_error(ve, 400)

            result = get_manager().move_bookmark(
                validated.source.model_dump(), validated.destination.model_dump()
            )
            return jsonify(
                SuccessResponse(
                    message="Bookmark moved successfully", data=result
                ).model_dump()
            )
        except (SectionNotFoundError, InvalidIndexError) as e:
            return handle_error(e, 404)
        except ValueError as e:
            return handle_error(e, 400)
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/export", methods=["GET"])
    def export_bookmarks():
        """Export all bookmarks as JSON."""
        try:
            data = get_manager().export_bookmarks()
            return jsonify(SuccessResponse(data=data).model_dump())
        except Exception as e:
            return handle_error(e, 500)

    @bookmarks_bp.route("/import", methods=["POST"])
    def import_bookmarks():
        """Import bookmarks from JSON."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = ImportBookmarksRequest(**data)
            except ValidationError as ve:
                return handle_error(ve, 400)

            get_manager().import_bookmarks(validated.data, validated.merge)
            return jsonify(
                SuccessResponse(message="Bookmarks imported successfully").model_dump()
            )
        except ValueError as e:
            return handle_error(e, 400)
        except Exception as e:
            return handle_error(e, 500)

    # Error handlers for the blueprint

    @bookmarks_bp.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return handle_error(Exception("Resource not found"), 404)

    @bookmarks_bp.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return handle_error(Exception("Internal server error"), 500)

    return bookmarks_bp


# Backward compatibility: create default blueprint instance
# This allows existing code that imports `bookmarks_api` to still work
bookmarks_api = create_bookmarks_blueprint()
