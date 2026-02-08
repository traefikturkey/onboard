"""API routes for layout widget ordering."""

import logging
from typing import Any

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from app.models.bookmark_api import ErrorResponse, SuccessResponse
from app.models.layout_api import ReorderWidgetsRequest

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

    def handle_error(
        e: Exception, status_code: int = 400
    ) -> tuple[dict[str, Any], int]:
        """Handle exceptions and return error response."""
        logger.error(f"API error: {e}")
        error_response = ErrorResponse(error=type(e).__name__, details=str(e))
        return error_response.model_dump(), status_code

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

    return layout_bp
