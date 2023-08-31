from PyQt5.QtCore import Qt
from qgis.utils import iface
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QVariant
from qgis.core import Qgis, QgsProject, QgsField, QgsMarkerSymbol, QgsVectorLayer, QgsRuleBasedRenderer, \
    QgsFeatureRequest
from PyQt5.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QLabel, QPushButton, QGridLayout, QApplication, \
    QProgressBar, QHBoxLayout

# Your classes
CLASSES = [
    {
        "class": "AFLORAMENTO ROCHOSO",
        "rgba": "50,168,82,77"
    },
    {
        "class": "APICUM",
        "rgba": "30,148,150,77"
    },
    {
        "class": "CULTURA ANUAL E PERENE",
        "rgba": "51,62,71,77"
    },
    {
        "class": "FLORESTA PLANTADA",
        "rgba": "99,197,204,77"
    },
    {
        "class": "FORMAÇÃO CAMPESTRE",
        "rgba": "17,149,14,77"
    },
    {
        "class": "FORMAÇÃO FLORESTAL",
        "rgba": "173,223,231,77"
    },
    {
        "class": "FORMAÇÃO SAVÂNICA",
        "rgba": "123,174,190,77"
    },
    {
        "class": "MANGUE",
        "rgba": "155,168,28,77"
    },
    {
        "class": "MINERAÇÃO",
        "rgba": "99,127,136,77"
    },
    {
        "class": "PASTAGEM",
        "rgba": "228,170,55,77"
    },
    {
        "class": "PRAIA E DUNA",
        "rgba": "171,132,126,77"
    },
    {
        "class": "RIO, LAGO E OCEANO",
        "rgba": "64,113,194,77"
    }
]


class LayerSelectionDockWidget(QDockWidget):
    def __init__(self, classes):
        super(LayerSelectionDockWidget, self).__init__()
        self.classes = None
        self.cls_selected = None
        self.progress_message_bar = None
        self.progress_bar = None
        self.widget = None
        self.init(classes)

    def init(self, classes):
        self.setWindowTitle("Fast Point Inspection")
        self.classes = classes
        self.cls_selected = None
        self.progress_message_bar = None
        self.progress_bar = None
        self.widget = QWidget()
        self.setWidget(self.widget)

        layout = QVBoxLayout()

        # Get the point layer from the project
        self.point_layer = self.get_point_layer()

        if self.point_layer is None:
            iface.messageBar().pushMessage(
                'POINTS GRID',
                'The grid with points was not found.',
                level=Qgis.Critical,
                duration=5,
            )
            return

        if self.point_layer is not None:
            self.zoom_to_5000()
            self.add_class_field()

        # Label to show the current selected class
        self.current_class_label = QLabel("Class not selected")
        self.current_class_label.setAlignment(Qt.AlignCenter)
        self.current_class_label.setStyleSheet("font-size: 25px;")
        layout.addWidget(self.current_class_label)
        self.set_feature_color()

        # Class buttons with grid layout
        self.class_buttons = []
        class_layout = QGridLayout()
        row, col = 0, 0
        for cls in classes:
            btn = QPushButton(cls["class"])
            btn.setStyleSheet(f"background-color: rgb({','.join(cls['rgba'].split(',')[:3])})")
            btn.clicked.connect(lambda _, cls=cls: self.on_class_selected(cls))
            btn.setCursor(Qt.PointingHandCursor)
            self.class_buttons.append(btn)

            class_layout.addWidget(btn, row, col)
            col += 1
            if col >= 2:  # Set the number of columns in the grid
                col = 0
                row += 1
        self.point_layer.selectionChanged.connect(self.set_class_for_selected_features)

        # Clear classification button
        clear_btn = QPushButton("Clear Classification")
        clear_btn.clicked.connect(self.clear_classification)
        clear_btn.setCursor(Qt.PointingHandCursor)

        layout.addLayout(class_layout)
        layout.addWidget(clear_btn)

        self.widget.setLayout(layout)

        # Add the dock widget to the QGIS interface
        iface.addDockWidget(Qt.RightDockWidgetArea, self)

    def reset(self):
        self.classes = None
        self.cls_selected = None
        self.progress_message_bar = None
        self.progress_bar = None
        self.widget = None

    def start_processing(self):
        # Remove existing progress bar if any
        if self.progress_message_bar:
            self.finish_progress()

        self.progress_message_bar = iface.messageBar().createMessage("")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)

        # Create a QWidget to hold the progress bar
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Processing..."))
        layout.addWidget(self.progress_bar)
        container.setLayout(layout)

        self.progress_message_bar.layout().addWidget(container)
        iface.messageBar().pushWidget(self.progress_message_bar, Qgis.Info)

    def update_progress(self, value):
        if self.progress_bar:
            self.progress_bar.setValue(value)
        else:
            self.start_processing()
            self.progress_bar.setValue(value)

    def finish_progress(self):
        if self.progress_message_bar:
            # Hide and remove the progress bar
            iface.messageBar().clearWidgets()
            self.progress_bar = None
            self.progress_message_bar = None

    def zoom_to_5000(self):
        # Set the extent to the layer's extent
        iface.mapCanvas().setExtent(self.point_layer.extent())

        # Set the scale to 1:5000
        iface.mapCanvas().zoomScale(5000)

        # Refresh the canvas
        iface.mapCanvas().refresh()

    def clear_classification(self):
        if self.point_layer is None:
            QApplication.instance().setOverrideCursor(Qt.ArrowCursor)
            return
        iface.actionSelectFreehand().trigger()
        self.current_class_label.setText("Removing Classification")
        self.current_class_label.setStyleSheet("background-color: none; font-size: 25px;")
        self.cls_selected = {
            "class": None,
            "rgba": "0,0,0,80"
        }

    def get_point_layer(self):
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == 0:  # 0: Point, 1: Line, 2: Polygon
                return layer
        return None

    def add_class_field(self):
        provider = self.point_layer.dataProvider()
        if provider.fieldNameIndex("class") == -1:
            field = QgsField("class", QVariant.String)
            provider.addAttributes([field])
            self.point_layer.updateFields()

    def on_class_selected(self, cls):
        self.cls_selected = cls
        self.current_class_label.setText(f"{cls['class']}")
        self.current_class_label.setStyleSheet(
            f"background-color: rgb({','.join(cls['rgba'].split(',')[:3])}); font-size: 25px;")
        iface.actionSelectFreehand().trigger()

    def set_class_for_selected_features(self):
        try:
            self.start_processing()
            cls = self.cls_selected

            if cls is None:
                iface.messageBar().pushMessage(
                    'ON_SET_CLASS',
                    "Please choose a class; none has been selected yet.",
                    level=Qgis.Critical,
                    duration=5,
                )
                self.update_progress(100)
                self.finish_progress()
                return

            selected_features = [feature.id() for feature in self.point_layer.selectedFeatures()]
            request = QgsFeatureRequest()
            request.setFilterFids(selected_features)
            # self.update_progress(10)

            rgba = [int(i) for i in cls['rgba'].split(',')]

            iface.mapCanvas().setSelectionColor(QColor(rgba[0], rgba[1], rgba[2], rgba[3]))

            all_features = list(self.point_layer.getFeatures(request))
            class_idx = self.point_layer.fields().indexOf('class')

            total_features = len(all_features)
            progress_per_feature = 70.0 / total_features

            self.point_layer.startEditing()

            attribute_map = {}

            for i, feature in enumerate(all_features):
                feature_id = feature.id()
                attributes = {class_idx: cls['class']}
                attribute_map[feature_id] = attributes

                self.update_progress(10 + (i + 1) * progress_per_feature)

            self.update_progress(80)
            self.point_layer.dataProvider().changeAttributeValues(attribute_map)

            self.point_layer.commitChanges()
            self.update_progress(90)
            self.set_feature_color()
            self.update_progress(100)
            self.finish_progress()
        except Exception as e:
            self.update_progress(100)
            self.finish_progress()
            iface.messageBar().pushMessage(
                'ON_SET_CLASS',
                "An error occurred while attempting to save the class.",
                level=Qgis.Critical,
                duration=5,
            )
            pass

    def set_feature_color(self):
        try:
            # Create default symbol and renderer
            symbol = QgsMarkerSymbol.createSimple({'name': 'square'})

            symbol_layer = symbol.symbolLayer(0)
            symbol_layer.setStrokeStyle(Qt.SolidLine)
            symbol_layer.setStrokeColor(QColor(0, 0, 0, 255))

            renderer = QgsRuleBasedRenderer(symbol)

            # Prepare rules
            rules = []
            for cls in self.classes:
                rgba = cls['rgba'].split(',')
                color = QColor(int(rgba[0]), int(rgba[1]), int(rgba[2]), int(rgba[3]))
                rules.append(
                    (cls['class'], f""" "class" = '{cls['class']}' """, color)
                )

            # Additional rule for NOT DEFINED
            rules.append(('NOT DEFINED', ' "class" is NULL ', QColor(0, 0, 0, 80)))

            # Set up the rule-based symbology
            root_rule = renderer.rootRule()

            for label, expression, color in rules:
                rule = root_rule.children()[0].clone()
                rule.setLabel(label)
                rule.setFilterExpression(expression)

                # Set color
                rule.symbol().setColor(color)

                # Remove border for all except 'NOT DEFINED'
                if label == 'NOT DEFINED':
                    rule.symbol().symbolLayer(0).setStrokeStyle(Qt.SolidLine)
                    rule.symbol().symbolLayer(0).setStrokeColor(QColor(0, 0, 0, 255))
                else:
                    rule.symbol().symbolLayer(0).setStrokeStyle(Qt.NoPen)

                root_rule.appendChild(rule)

            # Remove default rule
            root_rule.removeChildAt(0)

            # Apply the renderer to the layer
            self.point_layer.setRenderer(renderer)
            iface.layerTreeView().refreshLayerSymbology(self.point_layer.id())
            self.point_layer.triggerRepaint()
        except Exception as e:
            iface.messageBar().pushMessage(
                'ON_SET_FEATURE_COLOR',
                "Failed to Set Feature Color",
                level=Qgis.Critical,
                duration=5,
            )
            pass


LayerSelectionDockWidget(CLASSES)
