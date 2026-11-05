"""
Report service — generates ExaminationReport, KnowledgeProfile updates, and PDF exports.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.database.models import (
    AnswerEvaluation,
    DocumentTopic,
    Examination,
    ExaminationReport,
    KnowledgeProfile,
    TopicAssessment,
    TopicAssessmentStatus,
    User,
)

logger = logging.getLogger(__name__)


class ReportService:
    @staticmethod
    def generate_report(db: Session, examination: Examination) -> ExaminationReport:
        """Aggregate evaluation data into an ExaminationReport."""
        # Check if report already exists
        existing = (
            db.query(ExaminationReport)
            .filter(ExaminationReport.examination_id == examination.id)
            .first()
        )
        if existing:
            return existing

        evaluations = (
            db.query(AnswerEvaluation)
            .filter(AnswerEvaluation.examination_id == examination.id)
            .all()
        )

        if evaluations:
            # Weighted score: correctness 30%, completeness 25%, conceptual 20%, reasoning 15%, application 10%
            def weighted_score(ev: AnswerEvaluation) -> float:
                c = ev.correctness_score or 0.0
                comp = ev.completeness_score or 0.0
                con = ev.conceptual_score or 0.0
                r = ev.reasoning_score or 0.0
                a = ev.application_score or 0.0
                return c * 0.30 + comp * 0.25 + con * 0.20 + r * 0.15 + a * 0.10

            overall_score = sum(weighted_score(e) for e in evaluations) / len(evaluations)
        else:
            overall_score = 0.0

        assessments = (
            db.query(TopicAssessment)
            .filter(TopicAssessment.examination_id == examination.id)
            .all()
        )

        # Get topic names
        all_topics = db.query(DocumentTopic).filter(
            DocumentTopic.document_id == examination.document_id
        ).all()
        topic_name_map = {t.id: t.name for t in all_topics}

        topic_scores: dict = {}
        strong_concepts: list[str] = []
        weak_concepts_list: list[str] = []
        partial_concepts: list[str] = []
        not_assessed_concepts: list[str] = []

        for ta in assessments:
            topic_name = topic_name_map.get(ta.topic_id, f"Topic {ta.topic_id}")
            topic_scores[str(ta.topic_id)] = {
                "name": topic_name,
                "score": round(ta.strength_score or 0.0, 3),
                "status": ta.status.value,
                "questions_examined": ta.questions_examined,
            }
            if ta.status == TopicAssessmentStatus.STRONG:
                strong_concepts.append(topic_name)
            elif ta.status == TopicAssessmentStatus.WEAK:
                weak_concepts_list.append(topic_name)
            elif ta.status == TopicAssessmentStatus.PARTIALLY_UNDERSTOOD:
                partial_concepts.append(topic_name)
            else:
                not_assessed_concepts.append(topic_name)

        # Collect missing concepts and mistakes from evaluations
        missing_concepts: list[str] = []
        mistakes: list[str] = []
        for ev in evaluations:
            if ev.missing_concepts:
                missing_concepts.extend(ev.missing_concepts)
            if ev.mistakes_identified:
                mistakes.extend(ev.mistakes_identified)

        # Deduplicate
        missing_concepts = list(dict.fromkeys(missing_concepts))[:10]
        mistakes = list(dict.fromkeys(mistakes))[:10]

        # Build recommendations
        recommendations = ReportService._build_recommendations(
            overall_score=overall_score,
            weak_topics=[topic_name_map.get(ta.topic_id, "") for ta in assessments if ta.status == TopicAssessmentStatus.WEAK],
            partial_topics=[topic_name_map.get(ta.topic_id, "") for ta in assessments if ta.status == TopicAssessmentStatus.PARTIALLY_UNDERSTOOD],
            not_assessed=[topic_name_map.get(ta.topic_id, "") for ta in assessments if ta.status == TopicAssessmentStatus.NOT_ASSESSED],
        )

        provider_mode = evaluations[0].provider_mode if evaluations else "mock"

        report = ExaminationReport(
            examination_id=examination.id,
            user_id=examination.user_id,
            document_id=examination.document_id,
            overall_score=round(overall_score, 4),
            topic_scores=topic_scores,
            strong_concepts=strong_concepts,
            weak_concepts=weak_concepts_list,
            partial_concepts=partial_concepts,
            not_assessed_concepts=not_assessed_concepts,
            recommendations=recommendations,
            provider_mode=provider_mode,
            generated_at=datetime.now(timezone.utc),
        )
        db.add(report)

        # Update KnowledgeProfile
        ReportService._update_knowledge_profile(
            db=db,
            examination=examination,
            assessments=assessments,
            overall_score=overall_score,
        )

        db.commit()
        db.refresh(report)
        logger.info("Generated report for examination %d", examination.id)
        return report

    @staticmethod
    def _update_knowledge_profile(
        db: Session,
        examination: Examination,
        assessments: list[TopicAssessment],
        overall_score: float,
    ) -> None:
        """Create or update the user's KnowledgeProfile for this document."""
        profile = (
            db.query(KnowledgeProfile)
            .filter(
                KnowledgeProfile.user_id == examination.user_id,
                KnowledgeProfile.document_id == examination.document_id,
            )
            .first()
        )
        if not profile:
            profile = KnowledgeProfile(
                user_id=examination.user_id,
                document_id=examination.document_id,
            )
            db.add(profile)

        strong = [ta.topic_id for ta in assessments if ta.status == TopicAssessmentStatus.STRONG]
        weak = [ta.topic_id for ta in assessments if ta.status == TopicAssessmentStatus.WEAK]
        partial = [ta.topic_id for ta in assessments if ta.status == TopicAssessmentStatus.PARTIALLY_UNDERSTOOD]
        not_assessed = [ta.topic_id for ta in assessments if ta.status == TopicAssessmentStatus.NOT_ASSESSED]

        profile.strong_topics = strong
        profile.weak_topics = weak
        profile.partial_topics = partial
        profile.not_assessed_topics = not_assessed
        profile.overall_score = round(overall_score, 4)
        profile.total_examinations = (profile.total_examinations or 0) + 1
        profile.last_examination_id = examination.id
        profile.updated_at = datetime.now(timezone.utc)

    @staticmethod
    def _build_recommendations(
        overall_score: float,
        weak_topics: list[str],
        partial_topics: list[str],
        not_assessed: list[str],
    ) -> list[str]:
        recs: list[str] = []
        if overall_score >= 0.85:
            recs.append("Outstanding performance. Consider attempting more advanced examination challenges.")
        elif overall_score >= 0.70:
            recs.append("Good overall performance. Focus on deepening understanding of partially-understood topics.")
        elif overall_score >= 0.55:
            recs.append("Satisfactory performance. Revisit the topics marked as WEAK before the next examination.")
        else:
            recs.append("Performance indicates significant gaps. A thorough review of all topics is recommended.")

        if weak_topics:
            recs.append(f"Prioritise revision of: {', '.join(weak_topics[:3])}.")
        if partial_topics:
            recs.append(f"Consolidate understanding of: {', '.join(partial_topics[:3])}.")
        if not_assessed:
            recs.append(f"The following topics were not sufficiently examined: {', '.join(not_assessed[:3])}. Include these in the next session.")
        return recs

    @staticmethod
    def generate_pdf(
        db: Session,
        report: ExaminationReport,
        examination: Examination,
        user: User,
    ) -> bytes:
        """Generate a PDF report using ReportLab."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.colors import HexColor, black, white
            from reportlab.lib.units import mm, cm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                HRFlowable, KeepTogether,
            )
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
            import io as _io

            buffer = _io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm,
            )

            # Colours matching ExamForge palette
            TERRACOTTA = HexColor("#B8755D")
            CHARCOAL = HexColor("#302E2B")
            WARMGRAY = HexColor("#827B72")
            SAGE = HexColor("#788875")
            LAVENDER = HexColor("#A99AAF")
            IVORY = HexColor("#F6F2EB")
            SAND = HexColor("#E9DFD1")

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "Title", parent=styles["Title"],
                textColor=CHARCOAL, fontSize=22, spaceAfter=4,
                fontName="Helvetica-Bold",
            )
            subtitle_style = ParagraphStyle(
                "Subtitle", parent=styles["Normal"],
                textColor=WARMGRAY, fontSize=11, spaceAfter=16,
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
                        f"<font color='#827B72' size='9'>Mode: {(report.provider_mode or 'mock').upper()}</font>",
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
                        topic_data.append([f"Topic {_tid}", f"{round(float(tinfo)*100,1)}%", "—", "—"])

                topic_table = Table(topic_data, colWidths=[8*cm, 2.5*cm, 4.5*cm, 2.5*cm])
                topic_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), SAND),
                    ("TEXTCOLOR", (0, 0), (-1, 0), CHARCOAL),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, IVORY]),
                    ("GRID", (0, 0), (-1, -1), 0.5, SAND),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]))
                story.append(topic_table)
                story.append(Spacer(1, 12))

            # Strong / Weak / Partial
            def _concept_section(title: str, items: list[str], color) -> None:
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

            # Recommendations
            if report.recommendations:
                story.append(Paragraph("Revision Priorities", heading_style))
                for i, rec in enumerate(report.recommendations, 1):
                    story.append(Paragraph(f"{i}. {rec}", body_style))
                story.append(Spacer(1, 8))

            # Footer
            story.append(HRFlowable(width="100%", thickness=0.5, color=SAND, spaceAfter=6))
            story.append(Paragraph(
                "Generated by ExamForge — AI-Powered Autonomous Examination System",
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
