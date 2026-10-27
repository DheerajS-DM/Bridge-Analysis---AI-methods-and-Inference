from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt, QRectF
from core.schema import PartialOrderPlan

class GanttChartWidget(QWidget):
    """Custom PyQt6 QPainter Gantt Chart visualizer displaying Indian Standard (IRC)
    retrofit schedules, phase groupings, and cost breakdowns in INR."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.plan: PartialOrderPlan = None

    def set_plan(self, plan: PartialOrderPlan) -> None:
        self.plan = plan
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dark Slate Theme Background
        painter.fillRect(self.rect(), QColor("#11111b"))

        if not self.plan or not self.plan.steps:
            painter.setPen(QColor("#a6adc8"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No Retrofit Plan Synthesized. Engage 'Synthesize Indian Standard Retrofit Plan' to generate schedule.")
            return

        real_steps = [s for s in self.plan.steps if s.id not in ["Start", "Finish"]]
        total_inr = sum(getattr(step, "cost_inr", 0.0) for step in real_steps)
        total_days = sum(getattr(step, "duration_days", 0.0) + getattr(step, "curing_period_days", 0.0) for step in real_steps)

        # Summary Header
        painter.setPen(QColor("#cdd6f4"))
        header_text = f"IRC / BIS Structural Rehabilitation Schedule  |  Critical Path: {total_days:.0f} Days  |  Estimated Budget: INR {total_inr:,.0f} (Rs. {total_inr/1e5:.2f} Lakhs)"
        painter.drawText(20, 28, header_text)

        # Draw Day Grid Lines
        for day in range(1, 46, 3):
            x = 240 + (day - 1) * 22
            painter.setPen(QColor("#313244"))
            painter.drawLine(int(x), 40, int(x), self.height() - 20)
            painter.setPen(QColor("#6c7086"))
            painter.drawText(int(x) - 6, 38, f"D{day}")

        # Phase color palettes (subdued tones)
        phase_colors = {
            "emergency": QColor("#a63d40"),   # Subdued red
            "foundation": QColor("#3e5f76"),  # Muted deep blue
            "primary": QColor("#5b708b"),     # Steel blue
            "verification": QColor("#5a735a") # Olive green
        }

        y = 55
        current_day = 1.0

        for i, step in enumerate(real_steps):
            duration = max(getattr(step, "duration_days", 3.0), 1.0)
            curing = getattr(step, "curing_period_days", 0.0)
            cost_inr = getattr(step, "cost_inr", 0.0)
            code_ref = getattr(step, "standard_code", "IRC")

            bar_width = duration * 22
            start_x = 240 + (current_day - 1.0) * 22

            # Left Label: Task Name + Governing Standard
            painter.setPen(QColor("#cdd6f4"))
            label_text = f"{step.name[:26]} [{code_ref}]"
            painter.drawText(QRectF(15, y, 220, 30), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label_text)

            # Execution Bar
            phase = getattr(step, "phase", "primary")
            color = phase_colors.get(phase, QColor("#5b708b"))
            painter.setBrush(color)
            painter.setPen(QColor("#181825"))
            bar_rect = QRectF(start_x, y, bar_width, 28)
            painter.drawRoundedRect(bar_rect, 4, 4)

            # Curing Bar if applicable
            if curing > 0:
                cur_width = curing * 22
                cur_rect = QRectF(start_x + bar_width, y, cur_width, 28)
                painter.setBrush(QColor("#45475a"))
                painter.drawRoundedRect(cur_rect, 4, 4)
                painter.setPen(QColor("#a6adc8"))
                painter.drawText(cur_rect, Qt.AlignmentFlag.AlignCenter, f"Cure ({curing:.0f}d)")

            # Text inside execution bar
            cost_str = f"Rs.{cost_inr/1e5:.1f}L" if cost_inr >= 100000 else f"Rs.{cost_inr/1e3:.0f}k"
            painter.setPen(QColor("#ffffff"))
            painter.drawText(bar_rect, Qt.AlignmentFlag.AlignCenter, f"{cost_str}")

            y += 38
            current_day += (duration + curing)
