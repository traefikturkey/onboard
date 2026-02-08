"""API routes for layout widget ordering."""

import logging
from typing import Any

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from app.models.bookmark_api import ErrorResponse, SuccessResponse
from app.models.layout_api import (
    AddRowRequest,
    AddTabRequest,
    AddWidgetRequest,
    MoveWidgetRequest,
    ReorderWidgetsRequest,
)

logger = logging.getLogger(__name__)


def create_layout_blueprint(widget_order_manager=None):
    """
    Create layout API blueprint with optional injected widget order manager.

    Args:
        widget_order_manager: Optional WidgetOrderManager instance. If not provided,
                             uses the one from current_app.extensions.

    Returns:
        Configured Blueprint instance
    """
    layout_bp = Blueprint("layout_api", __name__, url_prefix="/api/layout")

    def get_manager():
        """Get the widget order manager from injection or current_app."""
        if widget_order_manager is not None:
            return widget_order_manager
        mgr = current_app.extensions.get("onboard_widget_order_manager")
        if mgr is not None:
            return mgr
        from app.services.widget_order_manager import WidgetOrderManager

        return WidgetOrderManager()

    def get_config_manager():
        """Get the layout config manager from current_app."""
        mgr = current_app.extensions.get("onboard_layout_config_manager")
        if mgr is not None:
            return mgr
        from app.services.layout_config_manager import LayoutConfigManager

        return LayoutConfigManager()

    def reload_layout():
        """Reload layout after config mutation."""
        layout = current_app.extensions.get("onboard_layout")
        if layout:
            layout.reload()

    def handle_error(
        e: Exception, status_code: int = 400
    ) -> tuple[dict[str, Any], int]:
        """Handle exceptions and return error response."""
        logger.error(f"API error: {e}")
        if status_code >= 500:
            error_response = ErrorResponse(error="InternalError", details="An internal error occurred")
        else:
            error_response = ErrorResponse(error=type(e).__name__, details=str(e))
        return error_response.model_dump(), status_code

    @layout_bp.before_request
    def csrf_check():
        """Reject cross-origin state-changing requests."""
        if request.method in ("POST", "DELETE", "PUT", "PATCH"):
            origin = request.headers.get("Origin") or request.headers.get("Referer")
            if not origin:
                return ErrorResponse(
                    error="Forbidden", details="Origin header required"
                ).model_dump(), 403
            from urllib.parse import urlparse
            parsed = urlparse(origin)
            request_host = request.host.split(":")[0]
            origin_host = parsed.hostname or ""
            if origin_host != request_host:
                return ErrorResponse(
                    error="Forbidden", details="Cross-origin request rejected"
                ).model_dump(), 403

    @layout_bp.route("/reorder", methods=["POST"])
    def reorder_widgets():
        """Reorder widgets across columns in a tab."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = ReorderWidgetsRequest(**data)
            except ValidationError as ve:
                return handle_error(ve, 400)

            get_manager().update_columns(
                validated.tab,
                [item.model_dump() for item in validated.columns],
            )
            return jsonify(
                SuccessResponse(
                    message="Widget order updated successfully"
                ).model_dump()
            )
        except Exception as e:
            return handle_error(e, 500)

    @layout_bp.route("/tabs", methods=["GET"])
    def get_tabs():
        """Return list of tab names."""
        try:
            names = get_config_manager().get_tab_names()
            return jsonify(SuccessResponse(data=names).model_dump())
        except Exception as e:
            return handle_error(e, 500)

    @layout_bp.route("/tabs", methods=["POST"])
    def add_tab():
        """Create a new tab."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = AddTabRequest(**data)
            except ValidationError as ve:
                return handle_error(ve, 400)

            try:
                get_config_manager().add_tab(validated.name)
            except ValueError as ve:
                return handle_error(ve, 409)

            reload_layout()
            return jsonify(
                SuccessResponse(message=f"Tab '{validated.name}' created").model_dump()
            ), 201
        except Exception as e:
            return handle_error(e, 500)

    @layout_bp.route("/tabs/<name>", methods=["DELETE"])
    def delete_tab(name):
        """Delete a tab by name."""
        try:
            try:
                get_config_manager().delete_tab(name)
            except ValueError as ve:
                msg = str(ve)
                if "not found" in msg.lower():
                    return handle_error(ve, 404)
                return handle_error(ve, 400)

            reload_layout()
            return jsonify(
                SuccessResponse(message=f"Tab '{name}' deleted").model_dump()
            )
        except Exception as e:
            return handle_error(e, 500)

    @layout_bp.route("/widgets", methods=["POST"])
    def add_widget():
        """Add a feed widget to a tab."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = AddWidgetRequest(**data)
            except ValidationError as ve:
                return handle_error(ve, 400)

            widget_data = {
                "name": validated.name,
                "type": "feed",
                "feed_url": validated.feed_url,
            }
            if validated.link:
                widget_data["link"] = validated.link

            try:
                widget_id = get_config_manager().add_widget(
                    validated.tab, widget_data, validated.col_index
                )
            except ValueError as ve:
                msg = str(ve)
                if "not found" in msg.lower():
                    return handle_error(ve, 404)
                return handle_error(ve, 400)

            reload_layout()
            return jsonify(
                SuccessResponse(
                    message="Widget added", data={"widget_id": widget_id}
                ).model_dump()
            ), 201
        except Exception as e:
            return handle_error(e, 500)

    @layout_bp.route("/move-widget", methods=["POST"])
    def move_widget():
        """Move a widget between tabs."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = MoveWidgetRequest(**data)
            except ValidationError as ve:
                return handle_error(ve, 400)

            try:
                get_config_manager().move_widget(
                    validated.widget_id,
                    validated.source_tab,
                    validated.dest_tab,
                    validated.dest_col_index,
                )
            except ValueError as ve:
                msg = str(ve)
                if "not found" in msg.lower():
                    return handle_error(ve, 404)
                return handle_error(ve, 400)

            # Clean up overlay for moved widget
            get_manager().remove_widget(validated.source_tab, validated.widget_id)

            reload_layout()
            return jsonify(
                SuccessResponse(message="Widget moved").model_dump()
            )
        except Exception as e:
            return handle_error(e, 500)

    @layout_bp.route("/rows", methods=["POST"])
    def add_row():
        """Add a new row to a tab."""
        try:
            data = request.get_json()
            if not data:
                return handle_error(ValueError("Request body is required"), 400)

            try:
                validated = AddRowRequest(**data)
            except ValidationError as ve:
                return handle_error(ve, 400)

            try:
                get_config_manager().add_row(validated.tab, validated.num_columns)
            except ValueError as ve:
                msg = str(ve)
                if "not found" in msg.lower():
                    return handle_error(ve, 404)
                return handle_error(ve, 400)

            reload_layout()
            return jsonify(
                SuccessResponse(message="Row added").model_dump()
            ), 201
        except Exception as e:
            return handle_error(e, 500)

    return layout_bp
