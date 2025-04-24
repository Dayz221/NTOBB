# app/PDFs.py
from flask import Blueprint, request, send_file, jsonify, current_app
from app.middleware.isAuthorized import isAuthorized
from app.pdf_converter import PDFConverter
from datetime import datetime

pdf_bp = Blueprint("pdf", __name__, url_prefix="/pdf")

@pdf_bp.route("/user", methods=["POST"])
@isAuthorized
def get_user_report(user):
    try:
        params = request.get_json(force=True) or {}
        start_ts = int(params.get("start_ts"))
        end_ts = int(params.get("end_ts"))

        if not start_ts or not end_ts:
            return jsonify({"message": "Не указаны start_ts или end_ts"}), 400

        period = f"{datetime.fromtimestamp(start_ts).strftime('%d.%m.%Y %H:%M')} – {datetime.fromtimestamp(end_ts).strftime('%d.%m.%Y %H:%M')}"

        converter = PDFConverter()
        pdf_stream = converter.generate_report_for_user(
            user_label=user.email,
            period=period,
            start_ts=start_ts,
            end_ts=end_ts
        )

        return send_file(
            pdf_stream,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{user.email}_report.pdf"
        )
    except Exception as ex:
        current_app.logger.exception("Ошибка генерации PDF для пользователя")
        return jsonify({"message": "Не удалось сформировать отчет"}), 500


@pdf_bp.route("/all_users", methods=["POST"])
@isAuthorized
def get_statistics_admin(user):
    try:
        params = request.get_json(force=True) or {}
        period = params.get("period")
        if not period:
            return jsonify({"message": "Не указан период"}), 400

        converter = PDFConverter()
        pdf_stream = converter.generate_report(
            user_label="Все пользователи",
            period=period
        )
        return send_file(
            pdf_stream,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="all_users_report.pdf"
        )
    except Exception as ex:
        current_app.logger.exception("Ошибка генерации PDF")
        return jsonify({"message": "Не удалось сформировать отчет"}), 500
