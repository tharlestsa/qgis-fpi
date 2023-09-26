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
        "class": "Afloramento Rochoso",
        "rgba": "255,170,95,77"
    },
    {
        "class": "Agricultura",
        "rgba": "233,116,237,77"
    },
    {
        "class": "Apicum",
        "rgba": "252,129,20,77"
    },
    {
        "class": "Aquicultura",
        "rgba": "9,16,119,77"
    },
    {
        "class": "Campo Alagado e Área Pantanosa",
        "rgba": "81,151,153,77"
    },
    {
        "class": "Floresta Alagável (beta)",
        "rgba": "2,105,117,77"
    },
    {
        "class": "Formação Campestre",
        "rgba": "214,188,116,77"
    },
    {
        "class": "Formação Florestal",
        "rgba": "31,141,73,77"
    },
    {
        "class": "Formação Savânica",
        "rgba": "125,201,117,77"
    },
    {
        "class": "Lavoura Perene",
        "rgba": "208,130,222,77"
    },
    {
        "class": "Lavoura Temporária",
        "rgba": "194,123,160,77"
    },
    {
        "class": "Mangue",
        "rgba": "4,56,29,77"
    },
    {
        "class": "Mineração",
        "rgba": "156,0,39,77"
    },
    {
        "class": "Mosaico de Usos",
        "rgba": "255,239,195,77"
    },
    {
        "class": "Outras Formações não Florestais",
        "rgba": "216,159,92,77"
    },
    {
        "class": "Outras Áreas não Vegetadas",
        "rgba": "219,77,79,77"
    },
    {
        "class": "Pastagem",
        "rgba": "237,222,142,77"
    },
    {
        "class": "Praia, Duna e Areal",
        "rgba": "255,160,122,77"
    },
    {
        "class": "Restinga Arbórea",
        "rgba": "2,214,89,77"
    },
    {
        "class": "Restinga Herbácea",
        "rgba": "173,81,0,77"
    },
    {
        "class": "Rio, Lago e Oceano",
        "rgba": "37,50,228,77"
    },
    {
        "class": "Silvicultura",
        "rgba": "122,89,0,77"
    },
    {
        "class": "Área Urbanizada",
        "rgba": "212,39,30,77"
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
        try:
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
                self.zoom()
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
        except Exception as e:
            iface.messageBar().pushMessage(
                'init',
                f"Error -> {e}",
                level=Qgis.Critical,
                duration=5,
            )
            pass

    def reset(self):
        self.classes = None
        self.cls_selected = None
        self.progress_message_bar = None
        self.progress_bar = None
        self.widget = None

    def start_processing(self):
        try:
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
        except Exception as e:
            iface.messageBar().pushMessage(
                'start_processing',
                f"Error -> {e}",
                level=Qgis.Critical,
                duration=5,
            )
            pass
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

    def zoom(self):
        try:
            # Set the extent to the layer's extent
            iface.mapCanvas().setExtent(self.point_layer.extent())
            self.point_layer.extent()

            # Set the scale to 1:5000
            iface.mapCanvas().zoomScale(5000)

            iface.mapCanvas().setDestinationCrs(self.point_layer.crs())

            # Refresh the canvas
            iface.mapCanvas().refreshAllLayers()
        except Exception as e:
            iface.messageBar().pushMessage(
                'ON_SET_CLASS',
                "An error occurred while attempting to save the class.",
                level=Qgis.Critical,
                duration=5,
            )
            pass

    def clear_classification(self):
        if self.point_layer is None:
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
            if isinstance(layer, QgsVectorLayer):
                return layer
        return None

    def add_class_field(self):
        provider = self.point_layer.dataProvider()
        if provider.fieldNameIndex("class") == -1:
            class_id = QgsField("class_id", QVariant.Int)
            _class = QgsField("class", QVariant.String)
            provider.addAttributes([class_id, _class])
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
            class_id_idx = self.point_layer.fields().indexOf('class_id')
            class_idx = self.point_layer.fields().indexOf('class')

            total_features = len(all_features)
            progress_per_feature = 70.0 / total_features

            self.point_layer.startEditing()

            attribute_map = {}

            for i, feature in enumerate(all_features):
                feature_id = feature.id()
                attributes = {class_id_idx: cls['class_id'], class_idx: cls['class']}
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

try:
    LayerSelectionDockWidget(CLASSES)
except Exception as e:
    print(f"{e}")
    pass