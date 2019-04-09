import sys
from math import sqrt

from PyQt5.QtCore import Qt, QSize, QTimer, QPoint, QRect
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame, QCheckBox, QHBoxLayout, QLineEdit, QPushButton, \
    QMessageBox

from graph import Graph


class TreeVisualizer(QWidget):

    def __init__(self):
        """Initial configuration."""
        super().__init__()

        # GLOBAL VARIABLES
        # graph variables
        self.graph = Graph()
        self.selected_node = None

        # functions for calculating forces
        self.repulsion_force_function = lambda x: 1 / x * 10
        self.attraction_force_function = lambda x, d=80: 0 if x <= d else -(x - d) / 10

        # offset of the mouse from the position of the currently dragged node
        self.mouse_drag_offset = None

        # position of the mouse; is updated when the mouse moves
        self.mouse_x = -1
        self.mouse_y = -1

        # variables for visualizing the graph
        self.node_radius = 20
        self.arrowhead_size = 4

        self.selected_node_color = Qt.red
        self.regular_node_color = Qt.white

        self.word_limit = 10  # limit the displayed length of words for each node

        # UI variables
        self.font_family = "Fira Code"
        self.font_size = 18

        # TIMERS
        self.simulation_timer = QTimer(interval=16, timeout=self.perform_simulation_iteration)

        # WIDGETS
        self.canvas = QFrame(self, minimumSize=QSize(600, 600))

        self.oriented_checkbox = QCheckBox(text="oriented", clicked=self.oriented_checkbox_change)

        self.labels_checkbox = QCheckBox(text="labels", clicked=self.labels_checkbox_change)
        self.labels_line_edit = QLineEdit(enabled=self.labels_checkbox.isChecked(),
                                          textChanged=self.labels_line_edit_change)

        self.help_button = QPushButton(text="?", clicked=self.help_button_clicked)

        # WIDGET LAYOUT
        self.main_v_layout = QVBoxLayout(self, margin=0)
        self.main_v_layout.addWidget(self.canvas)

        self.option_h_layout = QHBoxLayout(self, margin=10)
        self.option_h_layout.addWidget(self.oriented_checkbox)
        self.option_h_layout.addWidget(self.labels_checkbox)
        self.option_h_layout.addWidget(self.labels_line_edit)
        self.option_h_layout.addWidget(self.help_button)

        self.main_v_layout.addLayout(self.option_h_layout)

        self.setLayout(self.main_v_layout)

        # WINDOW SETTINGS
        self.setWindowTitle('Graph Visualizer in PyQt5!')
        self.setFont(QFont(self.font_family, self.font_size))
        self.show()

        # start the simulation
        self.simulation_timer.start()

    def help_button_clicked(self):
        """Is called when the help button is clicked; displays basic information about the application."""
        message = """
            <p>Welcome to <strong>Graph Visualizer</strong>.</p>
            <p>The app aims to help with creating, visualizing and exporting graphs. 
            It is powered by PyQt5 &ndash; a set of Python bindings for the C++ library Qt.</p>
            <p>See the app's <a href="https://github.com/xiaoxiae/GraphVisualizer">GitHub repository</a> for more.</p>
            <hr />
            <p>The controls are as follows:</p>
            <ul>
            <li><em>Left Mouse Button</em> &ndash; selects nodes and moves them around</li>
            <li><em>Right Mouse Button</em> &ndash; creates new nodes and vertices from the currently selected node</li>
            </ul>
        """

        QMessageBox.information(self, "About", message)

    def oriented_checkbox_change(self):
        """Is called when the oriented checkbox changes; sets the orientation of the graph."""
        self.graph.set_oriented(self.oriented_checkbox.isChecked())

    def labels_checkbox_change(self):
        """Is called when the label checkbox changes; enable/disable the labels line edit."""
        self.labels_line_edit.setEnabled(self.labels_checkbox.isChecked())

    def labels_line_edit_change(self, text):
        """Is called when the labels line edit changes; changes the name of the currently selected node. If the name
        exceeds the maximum displayed length of a node, turns the labels line edit red."""
        if self.selected_node is not None:
            self.selected_node.set_name(text)

        # set the background of the line edit color, according to whether the word is of appropriate length
        palette = self.labels_line_edit.palette()
        if len(text) > self.word_limit:
            palette.setColor(self.labels_line_edit.backgroundRole(), Qt.red)
        else:
            palette.setColor(self.labels_line_edit.backgroundRole(), Qt.white)
        self.labels_line_edit.setPalette(palette)

    def select_node(self, node):
        """Sets the selected node to the specified node and changes the text in labels line edit to its name."""
        self.selected_node = node
        self.labels_line_edit.setText(node.get_name())

    def mousePressEvent(self, event):
        """Is called when a mouse button is pressed; creates and moves nodes/vertices."""
        mouse_coordinates = self.get_mouse_coordinates(event)

        # if we are not on canvas, don't do anything
        if mouse_coordinates is None:
            return

        x = mouse_coordinates[0]
        y = mouse_coordinates[1]

        # (potentially) find a node that has been pressed
        pressed_node = None
        for node in self.graph.get_nodes():
            if self.distance(x, y, node.get_x(), node.get_y()) <= node.get_radius():
                pressed_node = node
                break

        # select/move node on left click
        # create new node/make a new connection on right click
        if event.button() == Qt.LeftButton:
            if pressed_node is not None:
                # select and move the node if it isn't already selected; else de-select it
                self.select_node(pressed_node)

                self.mouse_drag_offset = (x - self.selected_node.get_x(), y - self.selected_node.get_y())
                self.mouse_x = x
                self.mouse_y = y

        else:
            # either make/remove a connection, or create a new node
            if pressed_node is not None:
                if pressed_node is not self.selected_node:
                    # if a connection does not exist between the nodes, create it; otherwise remove it
                    if self.graph.does_vertice_exist(self.selected_node, pressed_node):
                        self.graph.remove_vertice(self.selected_node, pressed_node)
                    else:
                        self.graph.add_vertice(self.selected_node, pressed_node)
            else:
                # create a new node
                node = self.graph.add_node(x, y, self.node_radius)

                # if a selected node exists, connect it to the newly created node
                if self.selected_node is not None:
                    self.graph.add_vertice(self.selected_node, node)

                # make the newly created node the currently selected node
                self.select_node(node)

    def mouseReleaseEvent(self, event):
        """Is called when a mouse button is released; stops the drag."""
        self.mouse_drag_offset = None

    def mouseMoveEvent(self, event):
        """Is called when the mouse is moved across the window; updates mouse coordinates."""
        mouse_coordinates = self.get_mouse_coordinates(event, scale_down=True)

        self.mouse_x = mouse_coordinates[0]
        self.mouse_y = mouse_coordinates[1]

    def get_mouse_coordinates(self, event, scale_down=False):
        """Returns mouse coordinates if they are within the canvas and None if they are not. If scale_down is True, the
        function will scale down the coordinates to be within the canvas (useful for dragging) and return them."""
        x = event.pos().x()
        y = event.pos().y()

        # whether the coordinate components are on canvas
        x_on_canvas = 0 <= x <= self.canvas.width()
        y_on_canvas = 0 <= y <= self.canvas.height()

        # return scaled-down coordinates if scale_down is True
        if scale_down:
            return (x if x_on_canvas else 0 if x <= 0 else self.canvas.width(),
                    y if y_on_canvas else 0 if y <= 0 else self.canvas.height())
        else:
            return (x, y) if x_on_canvas and y_on_canvas else None

    def perform_simulation_iteration(self):
        """Performs one iteration of the simulation."""
        # evaluate forces that act upon the nodes
        for i in range(len(self.graph.get_nodes())):
            n1 = self.graph.get_nodes()[i]
            for j in range(i + 1, len(self.graph.get_nodes())):
                n2 = self.graph.get_nodes()[j]

                # calculate the distance of the nodes and their normalized vectors
                d = self.distance(n1.get_x(), n1.get_y(), n2.get_x(), n2.get_y())
                nx, ny = (n2.get_x() - n1.get_x()) / d, (n2.get_y() - n1.get_y()) / d

                # the size of the repel force between the two nodes
                fr = self.repulsion_force_function(d)

                # add the repel force to each of the nodes
                n1.add_force((-nx * fr, -ny * fr))
                n2.add_force((nx * fr, ny * fr))

                # if they are connected, add the leash force
                if self.graph.does_vertice_exist(n1, n2, ignore_orientation=True):
                    # the size of the repel force between the two nodes
                    fa = self.attraction_force_function(d)

                    # add the repel force to each of the nodes
                    n1.add_force((-nx * fa, -ny * fa))
                    n2.add_force((nx * fa, ny * fa))

            # since this node will not be visited again, evaluate the forces
            n1.evaluate_forces()

        # drag the selected node
        if self.selected_node is not None and self.mouse_drag_offset is not None:
            self.selected_node.set_x(self.mouse_x - self.mouse_drag_offset[0])
            self.selected_node.set_y(self.mouse_y - self.mouse_drag_offset[1])

        self.update()

    def paintEvent(self, event):
        """Paints the board."""
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.setPen(QPen(Qt.black, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))

        # bound the area to only draw on the canvas
        painter.setClipRect(0, 0, self.canvas.width(), self.canvas.height())

        # draw the background
        painter.drawRect(0, 0, self.canvas.width(), self.canvas.height())

        # draw vertices; has to be drawn before nodes, so they aren't drawn on top of them
        for node in self.graph.get_nodes():
            for neighbour in node.get_neighbours():
                x1, y1, x2, y2 = node.get_x(), node.get_y(), neighbour.get_x(), neighbour.get_y()

                # if it's oriented, draw an arrow
                if self.graph.is_oriented():
                    # calculate the position of the head of the arrow
                    # done by "shrinking" the distance from (x1, y1) to (x2, y2) by the radius of the node at (x2, y2)
                    d = self.distance(x1, y1, x2, y2)
                    ux, uy = (x2 - x1) / d, (y2 - y1) / d
                    r = neighbour.get_radius()

                    # the position of the head of the arrow
                    xa, ya = x1 + ux * (d - r), y1 + uy * (d - r)

                    # calculate the base of the arrow
                    # this is done the same way as the previous calculation
                    d = self.distance(x1, y1, xa, ya)
                    ux, uy = (xa - x1) / d, (ya - y1) / d

                    # position of the base of the arrow
                    x, y = x1 + ux * (d - self.arrowhead_size * 2), y1 + uy * (d - self.arrowhead_size * 2)

                    # the normal vectors to the unit vector of the arrow head
                    nx, ny = -uy, ux

                    painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
                    painter.drawPolygon(QPoint(xa, ya),
                                        QPoint(x + nx * self.arrowhead_size, y + ny * self.arrowhead_size),
                                        QPoint(x - nx * self.arrowhead_size, y - ny * self.arrowhead_size))

                painter.drawLine(x1, y1, x2, y2)

        # draw nodes
        for node in self.graph.get_nodes():
            # selected nodes are red; others are white
            if node is self.selected_node:
                painter.setBrush(QBrush(self.selected_node_color, Qt.SolidPattern))
            else:
                painter.setBrush(QBrush(self.regular_node_color, Qt.SolidPattern))

            # node information
            x, y, r = node.get_x(), node.get_y(), node.get_radius()

            painter.drawEllipse(QPoint(x, y), r, r)

            # if the label checkbox is checked, draw the names
            if self.labels_checkbox.isChecked():
                name = node.get_name()[:self.word_limit]

                # only draw the name, if it has characters
                if len(name) != 0:
                    # scale font down, depending on the length of the name of the node
                    painter.setFont(QFont(self.font_family, self.font_size / len(name)))

                    # draw the node name
                    painter.drawText(QRect(x - r, y - r, 2 * r, 2 * r), Qt.AlignCenter, name)

    def distance(self, x1, y1, x2, y2):
        """Returns the distance of two points in space."""
        return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


app = QApplication(sys.argv)
ex = TreeVisualizer()
sys.exit(app.exec_())