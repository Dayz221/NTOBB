# app/pdf_converter.py
import io
import os
import tempfile
from datetime import datetime

import matplotlib.pyplot as plt
from flask import current_app, send_file
from mongoengine.queryset.visitor import Q
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

from app.config import FONT_PATH, RATE_PER_CUBIC_METER
from app.models import User


class PDFConverter:
    def __init__(self,
                 rate_per_cubic_meter: float = RATE_PER_CUBIC_METER,
                 font_path: str = FONT_PATH):
        self.rate = rate_per_cubic_meter
        # Регистрируем шрифт один раз
        pdfmetrics.registerFont(TTFont('arial', font_path))

    def _parse_period(self, period: str):
        """Преобразует строку 'DD.MM.YYYY HH:MM – DD.MM.YYYY HH:MM' в два datetime."""
        try:
            start_s, end_s = period.split('–')
            start_dt = datetime.strptime(start_s.strip(), '%d.%m.%Y %H:%M')
            end_dt   = datetime.strptime(end_s.strip(), '%d.%m.%Y %H:%M')
            return int(start_dt.timestamp()), int(end_dt.timestamp())
        except ValueError:
            raise ValueError(
                'Неверный формат period. '
                'Нужно "DD.MM.YYYY HH:MM – DD.MM.YYYY HH:MM"'
            )

    def _collect_data(self,
                      start_ts: int,
                      end_ts: int,
                      building_id: int = None,
                      flat_id: int = None):
        """Собираем из базы всего: объём, ток, разбивку по минутам."""
        filt = Q(measures__timestamp__gte=start_ts) & Q(measures__timestamp__lte=end_ts)
        if building_id is not None:
            filt &= Q(building_id=building_id)
        if flat_id is not None:
            filt &= Q(flat_id=flat_id)

        users_qs = User.objects(filt).only('measures')
        total_volume = 0.0
        currents = []
        minute_volumes = {}

        for u in users_qs:
            for m in u.measures:
                if start_ts <= m.timestamp <= end_ts:
                    total_volume += m.volume
                    currents.append(m.current)
                    label = datetime.fromtimestamp(m.timestamp).strftime('%Y-%m-%d %H:%M')
                    minute_volumes[label] = minute_volumes.get(label, 0.0) + m.volume

        mean_power = sum(currents) / len(currents) if currents else 0.0
        price = total_volume * self.rate

        timestamps = sorted(minute_volumes.keys())
        volumes = [minute_volumes[t] for t in timestamps]
        return total_volume, mean_power, price, timestamps, volumes

    def _plot_trend(self, dates: list[str], values: list[float]) -> str:
        """Строит график и сохраняет его во временный PNG-файл."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            plt.figure()
            plt.plot(dates, values)
            plt.xlabel("Дата")
            plt.ylabel("Объём (м³)")
            plt.title("Тренд потребления воды")
            plt.tight_layout()
            plt.savefig(tmp.name)
            plt.close()
            return tmp.name

    def _build_pdf(self, data: dict, destination):
        """Собирает PDF-отчет по подготовленным данным."""
        doc = SimpleDocTemplate(
            destination, pagesize=A4,
            leftMargin=inch, rightMargin=inch,
            topMargin=inch, bottomMargin=inch
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="Body", parent=styles["Normal"],
            fontName="arial", fontSize=12
        ))
        styles.add(ParagraphStyle(
            name="TitleC", parent=styles["Heading1"],
            fontName="arial", alignment=1
        ))

        elems = [
            Paragraph("Отчёт по водопотреблению", styles["TitleC"]),
            Spacer(1, 12),
            Paragraph(f"<b>Пользователь:</b> {data['user']}", styles["Body"]),
            Paragraph(f"<b>Период:</b> {data['period']}", styles["Body"]),
            Spacer(1, 12),
        ]

        # Таблица со статистикой
        tbl_data = [["Метрика", "Значение"]]
        for m, v in data["stats"].items():
            tbl_data.append([m, f"{v:.2f}"])
        tbl = Table(tbl_data, colWidths=[3.5*inch, 2*inch])
        tbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "arial"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elems.append(tbl)
        elems.append(Spacer(1, 24))

        # График
        img_path = self._plot_trend(
            data["trend"]["dates"],
            data["trend"]["values"]
        )
        elems.append(RLImage(img_path, width=6*inch, height=3*inch))

        doc.build(elems)
        os.unlink(img_path)

    def generate_report(self,
                        user_label: str,
                        period: str,
                        building_id: int = None,
                        flat_id: int = None) -> io.BytesIO:
        """
        Основной метод: принимает метки, отдаёт BytesIO с готовым PDF.
        """
        start_ts, end_ts = self._parse_period(period)
        all_water, mean_power, price, dates, values = self._collect_data(
            start_ts, end_ts, building_id, flat_id
        )

        report_data = {
            "user": user_label,
            "period": period,
            "stats": {
                "Всего воды (м³)": all_water,
                "Средняя мощность (кВт)": mean_power,
                "Стоимость (Руб)": price
            },
            "trend": {
                "dates": dates,
                "values": values
            }
        }

        buf = io.BytesIO()
        self._build_pdf(report_data, buf)
        buf.seek(0)
        return buf
    
    def generate_report_for_user(self,
                                 user_label: str,
                                 period: str,
                                 start_ts: int,
                                 end_ts: int) -> io.BytesIO:
        """
        Генерирует отчет для одного пользователя на основе временного периода.
        """
        # Собираем данные для одного пользователя
        all_water, mean_power, price, dates, values = self._collect_data(
            start_ts=start_ts,
            end_ts=end_ts,
            building_id=None,  # Если нужно фильтровать по зданию, передайте соответствующий ID
            flat_id=None       # Если нужно фильтровать по квартире, передайте соответствующий ID
        )

        # Формируем данные для отчета
        report_data = {
            "user": user_label,
            "period": period,
            "stats": {
                "Всего воды (м³)": all_water,
                "Средняя мощность (кВт)": mean_power,
                "Стоимость (Руб)": price
            },
            "trend": {
                "dates": dates,
                "values": values
            }
        }

        # Создаем PDF-файл в памяти
        buf = io.BytesIO()
        self._build_pdf(report_data, buf)
        buf.seek(0)
        
        return buf
