from __future__ import annotations

from typing import Any, cast

from PySide6 import QtCore
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
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

        self.widgets: dict[str, QWidget] = {}
        self.labels: dict[str, QLabel] = {}
        self.source_labels: dict[str, QLabel] = {}

        # self.setMinimumWidth(500)

        self.initUI()
        self.retranslateUI()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _get_default(self, name: str) -> dict[str, Any]:
        return self.settings["defaults"][name]

    def _get_setting(
        self,
        name: str,
    ) -> tuple[dict[str, Any], str]:
        """
        Return the effective setting and its source.

        Precedence:

            environment > database > default
        """

        defaults = self.settings.get("defaults", {})

        if name not in defaults:
            raise KeyError(f"Unknown setting: {name}")

        env = self.settings.get("env", {})
        if name in env:
            return env[name], "env"

        db = self.settings.get("db", {})
        if name in db:
            return db[name], "db"

        return defaults[name], "defaults"

    def _get_effective_value(self, name: str) -> Any:
        setting, _ = self._get_setting(name)
        return setting

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def initUI(self) -> None:
        layout = QVBoxLayout(self)
        layout.addStretch()
        database_path_label = QLabel(str(db.getDBPath()), self)
        database_path_label.setObjectName("settingSource")
        database_path_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(database_path_label)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Defaults are the schema, so every setting displayed in the
        # dialog comes from here.
        for name, default_setting in self.settings["defaults"].items():
            setting, _ = self._get_setting(name)

            widget = self._create_widget(
                name=name,
                setting=default_setting,
                value=setting,
            )

            self.widgets[name] = widget
            self.labels[name] = QLabel()
            source_label = QLabel()
            source_label.setObjectName("settingSource")

            self.source_labels[name] = source_label

            value_layout = QVBoxLayout()
            value_layout.setContentsMargins(0, 0, 0, 0)
            value_layout.setSpacing(2)

            value_layout.addWidget(widget)
            value_layout.addWidget(source_label)

            form.addRow(self.labels[name], value_layout)

        layout.addLayout(form)

        self.close_button = QPushButton(self)
        self.close_button.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)
        layout.addStretch()

        self.setStyleSheet(
            """
            QLineEdit[differentFromDefault="true"],
            QComboBox[differentFromDefault="true"],
            QSpinBox[differentFromDefault="true"],
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
            QPushButton {
                text-align: left;
                padding-left: 10px;
            }
            """
        )

    def retranslateUI(self):
        self.setWindowTitle(
            QCoreApplication.translate("AppSettings", "Application Settings")
        )
        self.close_button.setText(QCoreApplication.translate("AppSettings", "Close"))
        for name, default_setting in self.settings["defaults"].items():
            _, source = self._get_setting(name)
            display_name = default_setting.get(
                "displayname",
                name,
            )

            description = default_setting.get(
                "description",
                "",
            )
            self.labels[name].setText(
                QCoreApplication.translate("AppSettings", display_name)
            )
            self.labels[name].setToolTip(
                QCoreApplication.translate("AppSettings", description)
            )
            self.widgets[name].setToolTip(
                QCoreApplication.translate("AppSettings", description)
            )
            if isinstance(self.widgets[name], QComboBox):
                for index, choice in enumerate(default_setting.get("choices", [])):
                    cast(QComboBox, self.widgets[name]).setItemText(
                        index,
                        QCoreApplication.translate(
                            "AppSettings",
                            str(choice),
                        ),
                    )
            self._update_visual_state(
                name,
                source,
            )

    def _set_bool_widget_text(self, value: bool, choices: list[str], widget: Any):
        if choices:
            widget.setText(
                QCoreApplication.translate("AppSettings", choices[int(value)])
            )

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

        if type_ == "bool":
            display_choices = setting.get("choices")
            if display_choices:
                widget = QPushButton()
                widget.setCheckable(True)
                widget.setProperty("textStateOnly", True)
                widget.setSizePolicy(
                    QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
                )
                self._set_bool_widget_text(widget.isChecked(), display_choices, widget)
                widget.toggled.connect(
                    lambda value, choices=display_choices, widget=widget: (
                        self._set_bool_widget_text(value, choices, widget)
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
            widget = QSpinBox()
            widget.setRange(
                -2_147_483_648,
                2_147_483_647,
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
                -1_000_000_000,
                1_000_000_000,
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
                    QCoreApplication.translate("AppSettings", str(choice)),
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

    # ------------------------------------------------------------------
    # Visual state
    # ------------------------------------------------------------------

    def _update_visual_state(
        self,
        name: str,
        source: str,
    ) -> None:
        widget = self.widgets[name]

        effective_value = self._get_effective_value(name)
        default_value = self._get_default(name).get("value")

        different_from_default = effective_value != default_value

        widget.setProperty(
            "differentFromDefault",
            different_from_default,
        )

        # Force stylesheet refresh after changing the dynamic property.
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
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

        elif isinstance(widget, QSpinBox):
            widget.blockSignals(True)
            widget.setValue(int(value))
            widget.blockSignals(False)

        elif isinstance(widget, QDoubleSpinBox):
            widget.blockSignals(True)
            widget.setValue(float(value))
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

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.retranslateUI()
        return super().changeEvent(event)
