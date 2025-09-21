import sys
import serial
import serial.tools.list_ports
from PyQt6 import QtWidgets, QtCore, QtGui, QtWebEngineWidgets
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
import requests  # 👈 para enviar datos al webhook

# ================= SERIAL =================
SERIAL_PORT = 'COM7'
BAUDRATE = 9600
WEBHOOK_URL = "https://innovafest2025.app.n8n.cloud/webhook/0cc43454-6a13-457b-93fe-47e0aa02f0fa"


class SerialThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(dict)
    raw_received = QtCore.pyqtSignal(str)

    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self._running = True

    def run(self):
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                while self._running:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        self.raw_received.emit(line)
                        if line.startswith("<") and line.endswith(">"):
                            line = line[1:-1]
                            parts = line.split(',')
                            if len(parts) == 16:
                                try:
                                    datos = {
                                        "numpaq": int(parts[0]),
                                        "lat": float(parts[1]),
                                        "lng": float(parts[2]),
                                        "alt": float(parts[3]),
                                        "pres": float(parts[4]),
                                        "temp": float(parts[5]),
                                        "acel": {"x": float(parts[6]), "y": float(parts[7]), "z": float(parts[8])},
                                        "giro": {"x": float(parts[9]), "y": float(parts[10]), "z": float(parts[11])},
                                        "mag": {"x": float(parts[12]), "y": float(parts[13]), "z": float(parts[14])},
                                        "paracaidas": parts[15].strip().lower() == "true"
                                    }

                                    # Emitir señal a la UI
                                    self.data_received.emit(datos)

                                    # 👇 Enviar automáticamente al webhook
                                    try:
                                        requests.post(WEBHOOK_URL, json=datos, timeout=2)
                                    except Exception as e:
                                        print("[ERROR Webhook]", e)

                                except Exception as e:
                                    print("[ERROR conversión]", e)
        except Exception as e:
            print("[ERROR Serial]", e)

    def stop(self):
        self._running = False
        self.wait()


# ================= SERIAL CONFIG WINDOW =================
class SerialConfigWindow(QtWidgets.QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Configuración de Puerto Serial")
        self.resize(400, 200)
        self.setStyleSheet("background-color: #0d0d0d; color: white;")
        self.main_window = main_window

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Selector de puerto
        self.port_combo = QtWidgets.QComboBox()
        self.refresh_ports()
        layout.addWidget(QtWidgets.QLabel("Puerto disponible:"))
        layout.addWidget(self.port_combo)

        # Botones
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_connect = QtWidgets.QPushButton("Conectar")
        self.btn_disconnect = QtWidgets.QPushButton("Desconectar")
        self.btn_refresh = QtWidgets.QPushButton("Actualizar")
        btn_layout.addWidget(self.btn_connect)
        btn_layout.addWidget(self.btn_disconnect)
        btn_layout.addWidget(self.btn_refresh)
        layout.addLayout(btn_layout)

        # Estado
        self.status_label = QtWidgets.QLabel("Estado: Desconectado")
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)

        # Eventos
        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btn_connect.clicked.connect(self.connect_serial)
        self.btn_disconnect.clicked.connect(self.disconnect_serial)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)

    def connect_serial(self):
        port = self.port_combo.currentText()
        if port:
            self.main_window.start_serial(port, BAUDRATE)
            self.status_label.setText(f"Estado: Conectado a {port}")
            self.status_label.setStyleSheet("color: lime;")

    def disconnect_serial(self):
        self.main_window.stop_serial()
        self.status_label.setText("Estado: Desconectado")
        self.status_label.setStyleSheet("color: red;")


# ================= MAP WINDOW =================
class MapWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mapa - CANSAT V1")
        self.resize(600, 400)
        self.setStyleSheet("background-color: #0d0d0d; color: white;")

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        title = QtWidgets.QLabel("🌍 Posición en Mapa")
        title.setStyleSheet("color:#00eaff; font-size:20px; font-weight:bold;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.web = QtWebEngineWidgets.QWebEngineView()
        self.web.setHtml("""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8"/>
                <title>Mapa CANSAT</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
                <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
                <style>
                    html, body, #map { height:100%; margin:0; padding:0; }
                </style>
            </head>
            <body>
                <div id="map"></div>
                <script>
                    var map = L.map('map').setView([0, 0], 2);
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        maxZoom: 19,
                        attribution: '© OpenStreetMap contributors'
                    }).addTo(map);

                    var path = L.polyline([], {color: 'red'}).addTo(map);
                    var marker = L.marker([0,0]).addTo(map);

                    function updatePos(lat, lng) {
                        var pos = [lat, lng];
                        path.addLatLng(pos);
                        marker.setLatLng(pos);
                        map.setView(pos, 15);
                    }
                </script>
            </body>
            </html>
        """)
        layout.addWidget(self.web)

    def update_position(self, lat, lng):
        js = f"updatePos({lat}, {lng});"
        self.web.page().runJavaScript(js)


# ================= 3D GYRO WINDOW =================
class Gyro3DWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Giroscopio 3D - CANSAT")
        self.resize(600, 400)
        self.setStyleSheet("background-color: #0d0d0d; color: white;")

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        title = QtWidgets.QLabel("🌀 Orientación 3D")
        title.setStyleSheet("color:#39ff14; font-size:20px; font-weight:bold;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Vista 3D ocupa más espacio
        self.view = gl.GLViewWidget()
        self.view.setCameraPosition(distance=15)
        layout.addWidget(self.view, stretch=3)  # Más espacio para el 3D

        # Cilindro
        self.cylinder = self.create_cylinder(radius=2, height=6, slices=40)
        self.view.addItem(self.cylinder)

        # Texto de ejes ocupa menos espacio
        self.label_axes = QtWidgets.QLabel("Roll (X)=0 | Pitch (Y)=0 | Yaw (Z)=0")
        self.label_axes.setStyleSheet("color:#39ff14; font-size:14px;")
        self.label_axes.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_axes, stretch=1)

    def create_cylinder(self, radius=1.0, height=2.0, slices=30):
        theta = np.linspace(0, 2*np.pi, slices)
        z = np.array([[-height/2], [height/2]])
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        verts = np.array([[x[i], y[i], z[j][0]] for i in range(len(theta)) for j in range(2)])
        
        faces = []
        for i in range(len(theta)-1):
            faces.append([2*i, 2*i+1, 2*i+3])
            faces.append([2*i, 2*i+3, 2*i+2])
        faces = np.array(faces)

        colors = np.array([[0.2, 0.7, 1, 1]] * len(faces))
        meshdata = gl.MeshData(vertexes=verts, faces=faces, faceColors=colors)
        return gl.GLMeshItem(meshdata=meshdata, smooth=True, drawFaces=True, drawEdges=True, edgeColor=(0,0,0,1))

    def update_rotation(self, gx, gy, gz):
        self.cylinder.resetTransform()
        self.cylinder.rotate(gx, 1, 0, 0)
        self.cylinder.rotate(gy, 0, 1, 0)
        self.cylinder.rotate(gz, 0, 0, 1)
        self.label_axes.setText(f"Roll (X)={gx} | Pitch (Y)={gy} | Yaw (Z)={gz}")


# ================= MAIN WINDOW =================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NIGHTRAPTOR - Estación de Tierra")
        self.resize(1400, 850)
        self.setStyleSheet("background-color: #0d0d0d; color: white;")
        self.serial_thread = None

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # HEADER
        header = QtWidgets.QHBoxLayout()

        # Logo pequeño del equipo 👇
        self.logo_team = QtWidgets.QLabel()
        self.logo_team.setPixmap(QtGui.QPixmap("logo_equipo.png"))  # cambia por tu archivo
        self.logo_team.setScaledContents(True)
        self.logo_team.setFixedSize(60, 60)
        header.addWidget(self.logo_team)

        # Logo TecNM
        self.logo_tecnm = QtWidgets.QLabel()
        self.logo_tecnm.setPixmap(QtGui.QPixmap("TecNM.png"))
        self.logo_tecnm.setScaledContents(True)
        self.logo_tecnm.setFixedSize(180, 80)
        header.addWidget(self.logo_tecnm)

        # Títulos
        title_box = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("NIGHTRAPTOR")
        title.setStyleSheet("color:#6f42c1; font-size:40px; font-weight:800;")
        title.setFont(QtGui.QFont("Agency FB", 48, QtGui.QFont.Weight.Bold))
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_box.addWidget(title)

        subtitle = QtWidgets.QLabel("SISTEMA DE CONTROL DE TIERRA - CANSAT")
        subtitle.setStyleSheet("color:#B2B0AD; font-size:14px;")
        subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_box.addWidget(subtitle)

        header.addLayout(title_box, stretch=1)

        # Logo ITSU
        self.logo_school = QtWidgets.QLabel()
        self.logo_school.setPixmap(QtGui.QPixmap("ITSU.png"))
        self.logo_school.setScaledContents(True)
        self.logo_school.setFixedSize(80, 80)
        header.addWidget(self.logo_school)

        layout.addLayout(header)

        # Botón Serial
        self.btn_serial_config = QtWidgets.QPushButton("⚙ Configuración Serial")
        self.btn_serial_config.clicked.connect(self.open_serial_config)
        layout.addWidget(self.btn_serial_config)

        # Telemetría Principal
        telem_layout = QtWidgets.QHBoxLayout()
        self.icon_telemetria = QtWidgets.QLabel()
        self.icon_telemetria.setPixmap(QtGui.QPixmap("antena.png"))
        self.icon_telemetria.setScaledContents(True)
        self.icon_telemetria.setFixedSize(35, 30)
        telem_layout.addWidget(self.icon_telemetria)

        self.telemetria = QtWidgets.QLabel("Paquete: -- | Lat: -- | Lng: -- | Alt: -- | Pres: -- | Temp: --")
        self.telemetria.setStyleSheet("color:#00eaff; font-size:16px;")
        telem_layout.addWidget(self.telemetria)

        layout.addLayout(telem_layout)

        # Estado de misión
        para_layout = QtWidgets.QHBoxLayout()
        self.icon_paracaidas = QtWidgets.QLabel()
        self.icon_paracaidas.setPixmap(QtGui.QPixmap("cohete.png"))
        self.icon_paracaidas.setScaledContents(True)
        self.icon_paracaidas.setFixedSize(35, 30)
        para_layout.addWidget(self.icon_paracaidas)

        self.paracaidas_label = QtWidgets.QLabel("Paracaídas: ---")
        self.paracaidas_label.setStyleSheet("color:red; font-size:16px;")
        para_layout.addWidget(self.paracaidas_label)

        layout.addLayout(para_layout)

        # IMU
        imu_layout = QtWidgets.QHBoxLayout()
        self.icon_imu = QtWidgets.QLabel()
        self.icon_imu.setPixmap(QtGui.QPixmap("grafica.png"))
        self.icon_imu.setScaledContents(True)
        self.icon_imu.setFixedSize(35, 30)
        imu_layout.addWidget(self.icon_imu)

        self.imu = QtWidgets.QLabel("Acel: (0,0,0) | Giro: (0,0,0) | Mag: (0,0,0)")
        self.imu.setStyleSheet("color:#39ff14; font-size:16px;")
        imu_layout.addWidget(self.imu)

        layout.addLayout(imu_layout)

        # Consola
        self.console = QtWidgets.QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFixedHeight(120)
        self.console.setStyleSheet("background-color:black; color:lime; font-family: Consolas; font-size:12px;")
        layout.addWidget(self.console)

        # Gráficas
        graphs_layout = QtWidgets.QHBoxLayout()

        self.graph_alt = pg.PlotWidget()
        self.graph_alt.setBackground('k')
        self.graph_alt.setFixedHeight(200)
        self.graph_alt.setLabel('left', 'Altitud')
        self.curve_alt = self.graph_alt.plot([], [], pen=pg.mkPen('c', width=2))
        graphs_layout.addWidget(self.graph_alt)

        self.graph_temp = pg.PlotWidget()
        self.graph_temp.setBackground('k')
        self.graph_temp.setFixedHeight(200)
        self.graph_temp.setLabel('left', 'Temperatura')
        self.curve_temp = self.graph_temp.plot([], [], pen=pg.mkPen('r', width=2))
        graphs_layout.addWidget(self.graph_temp)

        self.graph_pres = pg.PlotWidget()
        self.graph_pres.setBackground('k')
        self.graph_pres.setFixedHeight(200)
        self.graph_pres.setLabel('left', 'Presión')
        self.curve_pres = self.graph_pres.plot([], [], pen=pg.mkPen('y', width=2))
        graphs_layout.addWidget(self.graph_pres)

        layout.addLayout(graphs_layout)

        # Datos para gráficas
        self.x_data = []
        self.y_alt = []
        self.y_temp = []
        self.y_pres = []

        # Ventanas adicionales
        self.map_window = MapWindow()
        self.gyro3d_window = Gyro3DWindow()
        self.serial_config_window = SerialConfigWindow(self)
        self.map_window.show()
        self.gyro3d_window.show()

    def open_serial_config(self):
        self.serial_config_window.show()

    def start_serial(self, port, baudrate):
        if self.serial_thread:
            self.serial_thread.stop()
        self.serial_thread = SerialThread(port, baudrate)
        self.serial_thread.data_received.connect(self.update_ui)
        self.serial_thread.raw_received.connect(self.update_console)
        self.serial_thread.start()

    def stop_serial(self):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread = None

    def update_ui(self, datos):
        self.telemetria.setText(
            f"Paquete {datos['numpaq']} | Lat: {datos['lat']} | Lng: {datos['lng']} | Alt: {datos['alt']} m | Pres: {datos['pres']} hPa | Temp: {datos['temp']} °C")
        self.imu.setText(
            f"Acel: ({datos['acel']['x']}, {datos['acel']['y']}, {datos['acel']['z']}) | Giro: ({datos['giro']['x']}, {datos['giro']['y']}, {datos['giro']['z']}) | Mag: ({datos['mag']['x']}, {datos['mag']['y']}, {datos['mag']['z']})")
        self.paracaidas_label.setText("Paracaídas: " + ("✅ DESPLEGADO" if datos['paracaidas'] else "❌ CERRADO"))

        self.x_data.append(datos['numpaq'])
        self.y_alt.append(datos['alt'])
        self.y_temp.append(datos['temp'])
        self.y_pres.append(datos['pres'])
        self.curve_alt.setData(self.x_data, self.y_alt)
        self.curve_temp.setData(self.x_data, self.y_temp)
        self.curve_pres.setData(self.x_data, self.y_pres)

        # actualizar ventanas extra
        self.map_window.update_position(datos['lat'], datos['lng'])
        self.gyro3d_window.update_rotation(datos['giro']['x'], datos['giro']['y'], datos['giro']['z'])

    def update_console(self, raw):
        self.console.append(raw)


# ================= RUN =================
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
