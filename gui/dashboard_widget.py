import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout

class TelemetryDashboardWidget(QWidget):
    """Real-time telemetry and stress-strain curve canvas powered by PyQtGraph."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.win = pg.GraphicsLayoutWidget(show=True)
        layout.addWidget(self.win)

        # Plot 1: Elastic Modulus E(t) Decay
        self.p1 = self.win.addPlot(title="Elastic Modulus E(t) Degradation Curves")
        self.p1.setLabel('left', 'Modulus (Pa)')
        self.p1.setLabel('bottom', 'Time (Years)')
        self.curve1 = self.p1.plot(pen=pg.mkPen('r', width=2))

        self.win.nextRow()

        # Plot 2: von Mises Stress vs Yield Capacity
        self.p2 = self.win.addPlot(title="Peak von Mises Stress vs Allowable Yield Threshold")
        self.p2.setLabel('left', 'Stress (Pa)')
        self.p2.setLabel('bottom', 'Simulation Step')
        self.curve2 = self.p2.plot(pen=pg.mkPen('g', width=2))

    def update_modulus_plot(self, time_vec, modulus_vec):
        self.curve1.setData(time_vec, modulus_vec)

    def update_stress_plot(self, step_vec, stress_vec):
        self.curve2.setData(step_vec, stress_vec)
