"""Design tokens + Qt stylesheet matching the "Cyber-Precision / by RDS" dark theme."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Palette:
    # Surfaces
    background: str = "#0B141E"
    surface: str = "#0B141E"
    surface_lowest: str = "#060F18"
    surface_low: str = "#131C26"
    surface_mid: str = "#18202A"
    surface_high: str = "#222B35"
    surface_highest: str = "#2D3540"
    surface_bright: str = "#313A45"
    # Foreground
    on_surface: str = "#DAE3F1"
    on_surface_variant: str = "#B9CACB"
    outline: str = "#849495"
    outline_variant: str = "#3B494B"
    # Brand
    primary: str = "#00DBE9"
    primary_bright: str = "#00F0FF"
    primary_dim: str = "#007A80"
    on_primary: str = "#00363A"
    # Semantic
    success: str = "#00FF84"
    warning: str = "#FFB800"
    error: str = "#FF5C5C"
    error_container: str = "#93000A"


PALETTE = Palette()


def qss() -> str:
    """Global Qt stylesheet. Applied once on QApplication."""
    p = PALETTE
    return f"""
* {{
    font-family: "Space Grotesk", "Inter", "Segoe UI", "Helvetica Neue", sans-serif;
    color: {p.on_surface};
}}
QMainWindow, QWidget#RootWidget {{
    background: {p.background};
}}
QWidget {{
    background: transparent;
}}
QToolTip {{
    background: {p.surface_high};
    color: {p.on_surface};
    border: 1px solid {p.outline_variant};
    padding: 6px 10px;
}}
/* ----- Sidebar ----- */
QWidget#Sidebar {{
    background: #05070B;
    border-right: 1px solid {p.outline_variant};
}}
QLabel#BrandLabel {{
    color: {p.primary};
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.5px;
}}
QLabel#VersionLabel {{
    color: {p.outline};
    font-size: 11px;
}}
QPushButton#NavButton {{
    text-align: left;
    padding: 12px 20px;
    color: {p.outline};
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    font-size: 14px;
    font-weight: 500;
}}
QPushButton#NavButton:hover {{
    background: #0E1620;
    color: {p.on_surface};
}}
QPushButton#NavButton:checked {{
    background: {p.surface_mid};
    color: {p.primary};
    border-left: 3px solid {p.primary};
}}
/* ----- TopBar ----- */
QWidget#TopBar {{
    background: rgba(5, 7, 11, 0.85);
    border-bottom: 1px solid {p.outline_variant};
}}
QLabel#TopBarLabel {{
    color: {p.primary};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 3px;
}}
QLabel#StatusDot {{
    color: {p.outline_variant};
}}
/* ----- Cards ----- */
QFrame#Card {{
    background: {p.surface_low};
    border: 1px solid {p.outline_variant};
    border-radius: 8px;
}}
QFrame#CardLow {{
    background: {p.surface_mid};
    border: 1px solid {p.outline_variant};
    border-radius: 8px;
}}
QLabel#SectionTitle {{
    color: {p.on_surface};
    font-size: 24px;
    font-weight: 600;
    letter-spacing: -0.5px;
}}
QLabel#CardTitle {{
    color: {p.on_surface};
    font-size: 16px;
    font-weight: 600;
}}
QLabel#CardSubtitle {{
    color: {p.on_surface_variant};
    font-size: 13px;
}}
QLabel#LabelCaps {{
    color: {p.on_surface_variant};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
}}
QLabel#MonoData {{
    color: {p.on_surface};
    font-family: "Space Grotesk", monospace;
    font-size: 13px;
}}
QLabel#BigMetric {{
    color: {p.on_surface};
    font-size: 44px;
    font-weight: 300;
    letter-spacing: -1px;
}}
QLabel#BigMetricDim {{
    color: {p.outline};
    font-size: 44px;
    font-weight: 300;
    letter-spacing: -1px;
}}
/* ----- Buttons ----- */
QPushButton {{
    background: {p.surface_mid};
    border: 1px solid {p.outline_variant};
    padding: 8px 18px;
    color: {p.on_surface};
    font-weight: 600;
    border-radius: 4px;
}}
QPushButton:hover {{
    border-color: {p.primary};
    color: {p.primary};
}}
QPushButton:pressed {{
    background: {p.surface_high};
}}
QPushButton#PrimaryButton {{
    background: {p.primary};
    color: {p.on_primary};
    border: 1px solid {p.primary};
}}
QPushButton#PrimaryButton:hover {{
    background: {p.primary_bright};
}}
QPushButton#DangerButton {{
    color: {p.error};
}}
QPushButton#DangerButton:hover {{
    border-color: {p.error};
    color: {p.error};
}}
QPushButton#IconOnly {{
    border: none;
    background: transparent;
    padding: 6px;
    color: {p.outline};
}}
QPushButton#IconOnly:hover {{
    color: {p.primary};
}}
/* ----- Inputs ----- */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {{
    background: {p.surface_lowest};
    border: 1px solid {p.outline_variant};
    padding: 8px 10px;
    selection-background-color: {p.primary_dim};
    border-radius: 4px;
    color: {p.on_surface};
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {p.primary};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background: {p.surface_mid};
    border: 1px solid {p.outline_variant};
    selection-background-color: {p.primary_dim};
    selection-color: {p.on_primary};
}}
/* ----- Tab / Segment buttons ----- */
QTabBar::tab {{
    background: transparent;
    color: {p.outline};
    padding: 10px 16px;
    font-weight: 700;
    letter-spacing: 2px;
    border: none;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    color: {p.primary};
    border-bottom: 2px solid {p.primary};
}}
QTabWidget::pane {{
    border: none;
}}
/* ----- Toggle switch (custom QCheckBox styling) ----- */
QCheckBox::indicator {{
    width: 40px;
    height: 22px;
    border-radius: 11px;
    background: {p.surface_high};
    border: 1px solid {p.outline_variant};
}}
QCheckBox::indicator:checked {{
    background: {p.primary};
    border-color: {p.primary};
}}
/* ----- Scrollbars ----- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {p.surface_high};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {p.outline};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
/* ----- Lists ----- */
QListWidget, QTreeWidget, QTableWidget {{
    background: {p.surface_low};
    border: 1px solid {p.outline_variant};
    border-radius: 8px;
    outline: 0;
}}
QListWidget::item, QTreeWidget::item {{
    padding: 10px;
    border-bottom: 1px solid {p.outline_variant};
}}
QListWidget::item:selected {{
    background: {p.surface_mid};
    color: {p.primary};
    border-left: 3px solid {p.primary};
}}
QHeaderView::section {{
    background: {p.surface_low};
    color: {p.on_surface_variant};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {p.outline_variant};
    font-weight: 700;
    letter-spacing: 1.5px;
}}
/* ----- Separators ----- */
QFrame[frameShape="4"] {{
    color: {p.outline_variant};
    background-color: {p.outline_variant};
}}
    """
