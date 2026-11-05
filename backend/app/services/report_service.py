"""
Report service — generates ExaminationReport, KnowledgeProfile updates, and PDF exports.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.database.models import (
    Examination,
    ExaminationReport,
    User,
)

logger = logging.getLogger(__name__)


class ReportService:
    @staticmethod
    def generate_report(db: Session, examination: Examination) -> ExaminationReport:
        """Aggregate evaluation data and invoke Gemini Report Generation Agent."""
        existing = (
            db.query(ExaminationReport)
            .filter(ExaminationReport.examination_id == examination.id)
            .first()
        )
        if existing:
            return existing

        from app.agents.report_generation import ReportGenerationAgent
        return ReportGenerationAgent.generate(db=db, examination=examination)

    @staticmethod
    def generate_pdf(
        db: Session,
        report: ExaminationReport,
        examination: Examination,
        user: User,
    ) -> bytes:
        """Generate a PDF report using ReportLab with the ExamForge editorial aesthetic."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.colors import HexColor
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                HRFlowable,
            )

            buffer = __import__("io").BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm,
            )

            # ExamForge Editorial Colors
            TERRACOTTA = HexColor("#B8755D")
            CHARCOAL = HexColor("#302E2B")
            WARMGRAY = HexColor("#827B72")
            SAND = HexColor("#E9DFD1")
            IVORY = HexColor("#F6F2EB")
            SAGE = HexColor("#788875")
            LAVENDER = HexColor("#A99AAF")

            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                "Title", parent=styles["Heading1"],
                textColor=CHARCOAL, fontSize=22, spaceAfter=4,
                fontName="Helvetica-Bold",
            )
            subtitle_style = ParagraphStyle(
                "Subtitle", parent=styles["Normal"],
                textColor=WARMGRAY, fontSize=10, spaceAfter=14,
            )
            heading_style = ParagraphStyle(
                "Heading", parent=styles["Heading2"],
                textColor=TERRACOTTA, fontSize=13, spaceBefore=14, spaceAfter=6,
                fontName="Helvetica-Bold",
            )
            body_style = ParagraphStyle(
                "Body", parent=styles["Normal"],
                textColor=CHARCOAL, fontSize=10, spaceAfter=4, leading=16,
            )
            muted_style = ParagraphStyle(
                "Muted", parent=styles["Normal"],
                textColor=WARMGRAY, fontSize=9, spaceAfter=3,
            )

            story = []

            # Header
            story.append(Paragraph("ExamForge", ParagraphStyle(
                "Brand", parent=styles["Normal"],
                textColor=TERRACOTTA, fontSize=10, spaceAfter=2,
                fontName="Helvetica-Bold",
            )))
            story.append(Paragraph("Examination Assessment Report", title_style))
            story.append(Paragraph(
                f"Student: {user.name}  ·  Examination #{examination.id}  ·  "
                f"Generated: {report.generated_at.strftime('%d %B %Y')}",
                subtitle_style,
            ))
            story.append(HRFlowable(width="100%", thickness=1, color=SAND, spaceAfter=12))

            # Overall Score
            score_pct = round((report.overall_score or 0) * 100, 1)
            story.append(Paragraph("Overall Performance", heading_style))
            score_table = Table(
                [[
                    Paragraph(f"<b>{score_pct}%</b>", ParagraphStyle(
                        "Score", parent=styles["Normal"],
                        textColor=TERRACOTTA, fontSize=36, fontName="Helvetica-Bold",
                    )),
                    Paragraph(
                        f"<b>{_score_label(report.overall_score or 0)}</b><br/>"
                        f"<font color='#827B72' size='9'>AI Provider: {(report.provider_mode or 'live').upper()} (IBM Granite + Google Gemini)</font>",
                        body_style,
                    ),
                ]],
                colWidths=[5*cm, 12*cm],
            )
            score_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), IVORY),
                ("ROUNDEDCORNERS", [8]),
                ("PADDING", (0, 0), (-1, -1), 12),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(score_table)
            story.append(Spacer(1, 12))

            # Topic Scores
            if report.topic_scores:
                story.append(Paragraph("Topic-by-Topic Performance", heading_style))
                topic_data = [["Topic", "Score", "Status", "Questions"]]
                for _tid, tinfo in report.topic_scores.items():
                    if isinstance(tinfo, dict):
                        pct = round(tinfo.get("score", 0) * 100, 1)
                        topic_data.append([
                            tinfo.get("name", "Unknown"),
                            f"{pct}%",
                            tinfo.get("status", "—"),
                            str(tinfo.get("questions_examined", 0)),
                        ])
                    else:
                        topic_data.append([str(_tid), f"{round(float(tinfo)*100,1)}%", "—", "—"])

                topic_table = Table(topic_data, colWidths=[8*cm, 3*cm, 3.5*cm, 2.5*cm])
                topic_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), IVORY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), CHARCOAL),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.5, SAND),
                ]))
                story.append(topic_table)
                story.append(Spacer(1, 10))

            # Concept Breakdown
            def _concept_section(title: str, items: list, color):
                if not items:
                    return
                story.append(Paragraph(title, heading_style))
                for item in items[:8]:
                    story.append(Paragraph(f"• {item}", body_style))
                story.append(Spacer(1, 4))

            _concept_section("Strong Concepts", report.strong_concepts or [], SAGE)
            _concept_section("Partially Understood", report.partial_concepts or [], LAVENDER)
            _concept_section("Areas for Improvement", report.weak_concepts or [], TERRACOTTA)
            _concept_section("Not Assessed", report.not_assessed_concepts or [], WARMGRAY)

            # Recommendations / Revision Priorities
            if report.recommendations:
                story.append(Paragraph("Revision Priorities", heading_style))
                for i, rec in enumerate(report.recommendations, 1):
                    if isinstance(rec, dict):
                        topic_part = rec.get("topic", "General")
                        priority = rec.get("priority", "MEDIUM")
                        action = rec.get("action", rec.get("recommendation", ""))
                        rec_text = f"<b>[{priority}] {topic_part}</b>: {action}"
                    else:
                        rec_text = str(rec)
                    story.append(Paragraph(f"{i}. {rec_text}", body_style))
                story.append(Spacer(1, 8))

            # Footer
            story.append(HRFlowable(width="100%", thickness=0.5, color=SAND, spaceAfter=6))
            story.append(Paragraph(
                "Generated by ExamForge — AI-Powered Autonomous Examination System (Google Gemini + IBM Granite)",
                muted_style,
            ))

            doc.build(story)
            return buffer.getvalue()

        except ImportError:
            logger.warning("ReportLab not available — returning plain text report")
            return ReportService._generate_text_report(report, examination, user).encode("utf-8")

    @staticmethod
    def _generate_text_report(
        report: ExaminationReport,
        examination: Examination,
        user: User,
    ) -> str:
        lines = [
            "EXAMFORGE — EXAMINATION ASSESSMENT REPORT",
            "=" * 50,
            f"Student: {user.name}",
            f"Examination ID: {examination.id}",
            f"Date: {report.generated_at.strftime('%d %B %Y')}",
            "",
            f"Overall Score: {round((report.overall_score or 0) * 100, 1)}%",
            f"Assessment: {_score_label(report.overall_score or 0)}",
            f"AI Provider: {(report.provider_mode or 'live').upper()} (IBM Granite + Google Gemini)",
            "",
        ]
        if report.strong_concepts:
            lines.append("STRONG CONCEPTS:")
            lines.extend(f"  + {c}" for c in report.strong_concepts)
            lines.append("")
        if report.weak_concepts:
            lines.append("AREAS FOR IMPROVEMENT:")
            lines.extend(f"  - {c}" for c in report.weak_concepts)
            lines.append("")
        if report.recommendations:
            lines.append("RECOMMENDATIONS:")
            for i, rec in enumerate(report.recommendations, 1):
                if isinstance(rec, dict):
                    topic_part = rec.get("topic", "General")
                    priority = rec.get("priority", "MEDIUM")
                    action = rec.get("action", rec.get("recommendation", ""))
                    lines.append(f"  {i}. [{priority}] {topic_part}: {action}")
                else:
                    lines.append(f"  {i}. {rec}")
        return "\n".join(lines)


def _score_label(score: float) -> str:
    if score >= 0.85:
        return "Excellent"
    elif score >= 0.70:
        return "Good"
    elif score >= 0.55:
        return "Satisfactory"
    elif score >= 0.40:
        return "Needs Improvement"
    else:
        return "Poor"
