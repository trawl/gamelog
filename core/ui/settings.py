"""Application settings dialog for viewing and editing effective settings."""

from __future__ import annotations

from typing import Any

from PySide6 import QtCore
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.engine.db import db
from core.engine.settings import appsettings


class SettingsDialog(QDialog):
    """
    Application settings dialog.

    Setting precedence:

        environment > database > default

    The defaults dictionary is the authoritative schema and contains
    display metadata such as displayname, description and choices.

    Database and environment settings only contain value/type information.

    Changes are persisted to the database immediately.
    """

    settingChanged = QtCore.Signal(str, object)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.settings = appsettings.getSettings()
        self.game_settings = appsettings.getGameSettings()

        self.widgets: dict[str, QWidget] = {}
        self.labels: dict[str, QLabel] = {}
        self.source_labels: dict[str, QLabel] = {}
        self.reset_buttons: dict[str, QPushButton] = {}

        self.initUI()
        self.retranslateUI()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _all_defaults(self) -> dict[str, Any]:
        merged = dict(self.settings["defaults"])
        for gsettings in self.game_settings.values():
            merged.update(gsettings)
        return merged

    def _get_default(self, name: str) -> dict[str, Any]:
        all_defaults = self._all_defaults()
        if name not in all_defaults:
            raise KeyError(f"Unknown setting: {name}")
        return all_defaults[name]

    def _get_setting(
        self,
        name: str,
    ) -> tuple[Any, str]:
        """Return the effective setting value and its source (env/db/defaults)."""
        if name not in self._all_defaults():
            raise KeyError(f"Unknown setting: {name}")

        # Game settings are stored in appsettings separately from self.settings.
        # Delegate to appsettings for any key not in core settings defaults.
        if name not in self.settings["defaults"]:
            value = appsettings[name]
            default = self._get_default(name)["value"]
            if value is None or value == default:
                return default, "defaults"
            return value, "db"

        env = self.settings.get("env", {})
        if name in env:
            return env[name], "env"

        db_vals = self.settings.get("db", {})
        if name in db_vals:
            return db_vals[name], "db"

        return self._get_default(name)["value"], "defaults"

    def _get_effective_value(self, name: str) -> Any:
        setting, _ = self._get_setting(name)
        return setting

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def initUI(self) -> None:
        """Build the settings dialog: category list on the left, form on the right."""
        layout = QVBoxLayout(self)

        database_path_label = QLabel(str(db.getDBPath()), self)
        database_path_label.setObjectName("settingSource")
        database_path_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(database_path_label)

        # Main area: list + stacked pages
        body = QHBoxLayout()
        body.setSpacing(0)
        layout.addLayout(body)

        self.category_list = QListWidget(self)
        self.category_list.setFixedWidth(140)
        self.category_list.setSpacing(2)
        self.category_list.setSizeAdjustPolicy(
            QListWidget.SizeAdjustPolicy.AdjustToContents
        )
        self.category_list.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        body.addWidget(self.category_list)

        self.stack = QStackedWidget(self)
        body.addWidget(self.stack, stretch=1)

        # "General" page — core settings
        self._general_item = QListWidgetItem("")
        self.category_list.addItem(self._general_item)
        self.stack.addWidget(self._make_scroll_page(self.settings["defaults"]))

        # One page per game that has registered settings
        self._game_items: dict[str, QListWidgetItem] = {}
        for game_name, gsettings in self.game_settings.items():
            item = QListWidgetItem(game_name)
            self.category_list.addItem(item)
            self._game_items[game_name] = item
            self.stack.addWidget(self._make_scroll_page(gsettings))

        self.category_list.setCurrentRow(0)
        self.category_list.currentRowChanged.connect(self.stack.setCurrentIndex)

        # self.resize(640, 480)

        self.close_button = QPushButton(self)
        self.close_button.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.setStyleSheet(
            """
            QLineEdit[differentFromDefault="true"],
            ScoreSpinBox[differentFromDefault="true"],
            QComboBox[differentFromDefault="true"],
            QDoubleSpinBox[differentFromDefault="true"],
            QPushButton[differentFromDefault="true"],
            QCheckBox[differentFromDefault="true"] {
                border: 1px solid #e0b400;
                font-weight: bold;
            }

            QLabel#settingSource {
                color: #777;
                font-size: 11px;
            }
            QPushButton[textStateOnly="true"] {
                text-align: left;
                padding-left: 10px;
            }
            QPushButton[resetButton="true"] {
                font-size: 14px;
                padding: 0px;
                border: none;
                color: #888;
            }
            QPushButton[resetButton="true"]:hover {
                color: #e0b400;
            }
            QPushButton[resetButton="true"]:disabled {
                color: transparent;
            }
            """
        )

    def _make_scroll_page(self, settings_dict: dict) -> QWidget:
        """Build a category page containing its settings form."""
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.addStretch()
        page_layout.addLayout(self._build_form(settings_dict))
        page_layout.addStretch()
        return page

    def _build_form(self, settings_dict: dict) -> QFormLayout:
        """Build a QFormLayout for the given settings schema dict."""
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        for name, default_setting in settings_dict.items():
            setting, _ = self._get_setting(name)
            widget = self._create_widget(
                name=name, setting=default_setting, value=setting
            )
            self.widgets[name] = widget
            self.labels[name] = QLabel()
            source_label = QLabel()
            source_label.setObjectName("settingSource")
            self.source_labels[name] = source_label
            reset_btn = QPushButton("↺")
            reset_btn.setFixedSize(24, 24)
            reset_btn.setProperty("resetButton", True)
            reset_btn.setToolTip(
                QCoreApplication.translate("AppSettings", "Reset to default")
            )
            reset_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            reset_btn.clicked.connect(lambda _, n=name: self._reset_to_default(n))
            self.reset_buttons[name] = reset_btn
            widget_row = QHBoxLayout()
            widget_row.setContentsMargins(0, 0, 0, 0)
            widget_row.setSpacing(4)
            widget_row.addWidget(widget)
            widget_row.addWidget(reset_btn)
            value_layout = QVBoxLayout()
            value_layout.setContentsMargins(0, 0, 0, 0)
            value_layout.setSpacing(2)
            value_layout.addLayout(widget_row)
            value_layout.addWidget(source_label)
            form.addRow(self.labels[name], value_layout)
        return form

    def retranslateUI(self) -> None:
        """Re-apply translated labels, tooltips and choices to every widget."""
        self.setWindowTitle(
            QCoreApplication.translate("AppSettings", "Application Settings")
        )
        self.close_button.setText(QCoreApplication.translate("AppSettings", "Close"))
        self._general_item.setText(QCoreApplication.translate("AppSettings", "General"))
        for game_name, item in self._game_items.items():
            item.setText(QCoreApplication.translate("AppSettings", game_name))

        all_defaults = self._all_defaults()
        for name, default_setting in all_defaults.items():
            if name not in self.widgets:
                continue
            _, source = self._get_setting(name)
            context = default_setting.get("context", "AppSettings")
            display_name = default_setting.get("displayname", name)
            description = default_setting.get("description", "")
            self.labels[name].setText(QCoreApplication.translate(context, display_name))
            self.labels[name].setToolTip(
                QCoreApplication.translate(context, description)
            )
            self.widgets[name].setToolTip(
                QCoreApplication.translate(context, description)
            )
            choices = default_setting.get("choices", [])
            widget = self.widgets[name]
            if isinstance(widget, QComboBox):
                for index, choice in enumerate(choices):
                    widget.setItemText(
                        index,
                        QCoreApplication.translate(context, str(choice)),
                    )
            elif isinstance(widget, QPushButton) and widget.isCheckable() and choices:
                self._set_bool_widget_text(widget.isChecked(), choices, widget, context)
            self._update_visual_state(name, source)

    def _set_bool_widget_text(
        self, value: bool, choices: list[str], widget: Any, context: str = "AppSettings"
    ) -> None:
        if choices:
            widget.setText(QCoreApplication.translate(context, choices[int(value)]))

    def _create_widget(
        self,
        name: str,
        setting: dict[str, Any],
        value: Any,
    ) -> QWidget:
        """
        Create a widget based on the schema in defaults.

        `setting` always comes from defaults, so type/choices/etc.
        are guaranteed to be available here.
        """

        type_ = setting.get("type", "str")
        choices = setting.get("choices")
        context = setting.get("context", "AppSettings")

        if type_ == "bool":
            display_choices = setting.get("choices")
            if display_choices:
                widget = QPushButton()
                widget.setCheckable(True)
                widget.setProperty("textStateOnly", True)
                widget.setProperty("boolChoices", display_choices)
                widget.setProperty("boolContext", context)
                widget.setSizePolicy(
                    QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
                )
                self._set_bool_widget_text(
                    widget.isChecked(), display_choices, widget, context
                )
                widget.toggled.connect(
                    lambda value, choices=display_choices, widget=widget, ctx=context: (
                        self._set_bool_widget_text(value, choices, widget, ctx)
                    )
                )
            else:
                widget = QCheckBox()
            widget.setChecked(bool(value))

            widget.toggled.connect(
                lambda value, name=name: self._value_changed(name, value)
            )

            return widget

        if type_ == "int":
            from core.ui.game import ScoreSpinBox

            widget = ScoreSpinBox()
            widget.setRange(
                setting.get("min", -2_147_483_648),
                setting.get("max", 2_147_483_647),
            )

            if value is not None:
                widget.setValue(int(value))

            widget.valueChanged.connect(
                lambda value, name=name: self._value_changed(name, value)
            )

            return widget

        if type_ == "float":
            widget = QDoubleSpinBox()
            widget.setRange(
                setting.get("min", -1_000_000_000),
                setting.get("max", 1_000_000_000),
            )
            widget.setDecimals(6)

            if value is not None:
                widget.setValue(float(value))

            widget.valueChanged.connect(
                lambda value, name=name: self._value_changed(name, value)
            )

            return widget

        if type_ == "str" and choices:
            widget = QComboBox()
            widget.setSizePolicy(
                QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
            )
            for choice in choices:
                widget.addItem(
                    QCoreApplication.translate(context, str(choice)),
                    userData=choice,
                )

            index = widget.findData(value)

            if index >= 0:
                widget.setCurrentIndex(index)

            widget.currentIndexChanged.connect(
                lambda _index, name=name, widget=widget: self._value_changed(
                    name,
                    widget.currentData(),
                )
            )

            return widget

        # Default widget for str and unknown types.
        widget = QLineEdit()

        if value is not None:
            widget.setText(str(value))

        widget.editingFinished.connect(
            lambda name=name, widget=widget: self._value_changed(
                name,
                widget.text(),
            )
        )

        return widget

    # ------------------------------------------------------------------
    # Changes
    # ------------------------------------------------------------------

    def _value_changed(
        self,
        name: str,
        value: Any,
    ) -> None:
        """Persist an edited setting and refresh its effective value/state."""
        # Type information comes exclusively from defaults.
        default_setting = self._get_default(name)
        type_ = default_setting.get("type", "str")

        value = self._convert_value(
            value,
            type_,
        )

        self.save_setting(
            name,
            value,
            type_,
        )

        # Update the in-memory database representation.
        self.settings.setdefault("db", {})[name] = value

        # Recalculate the effective value because env > db > default.
        effective_value = self._get_effective_value(name)
        _, source = self._get_setting(name)

        self._set_widget_value(
            self.widgets[name],
            effective_value,
        )

        self._update_visual_state(
            name,
            source,
        )

    def _reset_to_default(self, name: str) -> None:
        """Reset a setting to its schema default and persist the change."""
        default_value = self._get_default(name)["value"]
        type_ = self._get_default(name).get("type", "str")
        self.save_setting(name, default_value, type_)
        # Remove from db layer so the default wins again.
        self.settings.get("db", {}).pop(name, None)
        appsettings.set(name, default_value, persistent=True)
        self._set_widget_value(self.widgets[name], default_value)
        _, source = self._get_setting(name)
        self._update_visual_state(name, source)

    # ------------------------------------------------------------------
    # Visual state
    # ------------------------------------------------------------------

    def _update_visual_state(
        self,
        name: str,
        source: str,
    ) -> None:
        """Highlight non-default widgets and label each with its source."""
        widget = self.widgets[name]

        effective_value = self._get_effective_value(name)
        default_value = self._get_default(name).get("value")

        different_from_default = effective_value != default_value

        from core.ui.game import ScoreSpinBox

        if isinstance(widget, ScoreSpinBox):
            # ScoreSpinBox sets an inline stylesheet on its QLineEdit which
            # overrides parent property-based selectors, so apply the gold
            # border directly to the line_edit's own stylesheet.
            le = widget.lineEdit()
            base = widget._text_css_colourless
            if different_from_default:
                base += "QLineEdit { border: 1px solid #e0b400; font-weight: bold; }"
            le.setStyleSheet(base)
        else:
            widget.setProperty("differentFromDefault", different_from_default)
            # Force stylesheet refresh after changing the dynamic property.
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
        if name in self.reset_buttons:
            self.reset_buttons[name].setEnabled(different_from_default)

        source_names = {
            "env": QCoreApplication.translate(
                "AppSettings",
                "Environment",
            ),
            "db": QCoreApplication.translate(
                "AppSettings",
                "Database",
            ),
            "defaults": QCoreApplication.translate(
                "AppSettings",
                "Default",
            ),
        }
        self.source_labels[name].setText(
            QCoreApplication.translate("AppSettings", source_names.get(source, source))
        )

    # ------------------------------------------------------------------
    # Widget values
    # ------------------------------------------------------------------

    @staticmethod
    def _set_widget_value(
        widget: QWidget,
        value: Any,
    ) -> None:
        from core.ui.game import ScoreSpinBox

        if isinstance(widget, QCheckBox):
            widget.blockSignals(True)
            widget.setChecked(bool(value))
            widget.blockSignals(False)

        elif isinstance(widget, QComboBox):
            widget.blockSignals(True)
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)
            widget.blockSignals(False)

        elif isinstance(widget, ScoreSpinBox):
            widget.blockSignals(True)
            widget.setValue(int(value))
            widget.blockSignals(False)

        elif isinstance(widget, QDoubleSpinBox):
            widget.blockSignals(True)
            widget.setValue(float(value))
            widget.blockSignals(False)

        elif isinstance(widget, QPushButton) and widget.isCheckable():
            widget.blockSignals(True)
            widget.setChecked(bool(value))
            choices = widget.property("boolChoices")
            context = widget.property("boolContext") or "AppSettings"
            if choices:
                from PySide6.QtCore import QCoreApplication

                widget.setText(
                    QCoreApplication.translate(context, choices[int(bool(value))])
                )
            widget.blockSignals(False)

        elif isinstance(widget, QLineEdit):
            widget.blockSignals(True)
            widget.setText("" if value is None else str(value))
            widget.blockSignals(False)

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    @staticmethod
    def _convert_value(
        value: Any,
        type_: str,
    ) -> Any:
        if value is None:
            return None

        if type_ == "bool":
            return bool(value)

        if type_ == "int":
            return int(value)

        if type_ == "float":
            return float(value)

        if type_ == "str":
            return str(value)

        return value

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_setting(
        self,
        name: str,
        value: Any,
        type_: str,
    ) -> None:
        """
        Persist a setting to the database.
        """

        appsettings.set(name, value, persistent=True)
        self.settingChanged.emit(name, value)

    def changeEvent(self, event: QEvent) -> None:
        """Retranslate the dialog when the application language changes."""
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.retranslateUI()
        return super().changeEvent(event)
