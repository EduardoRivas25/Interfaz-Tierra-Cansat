# 🛰️ NIGHTRAPTOR - Estación de Tierra CANSAT

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PyQt6](https://img.shields.io/badge/Framework-PyQt6-6f42c1.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**NIGHTRAPTOR** es una estación de control terrestre (GCS) desarrollada en Python para el monitoreo en tiempo real de un CanSat. El sistema permite procesar telemetría serial, visualizar la posición en mapas dinámicos y analizar la orientación 3D del dispositivo.

---

## 🚀 Características Principales

* **📈 Telemetría en Tiempo Real**: Visualización de número de paquete, altitud, temperatura, presión atmosférica y estado del paracaídas.
* **🌍 Rastreo GPS**: Integración con un mapa interactivo (Leaflet) que actualiza la posición y dibuja la trayectoria del CanSat.
* **🌀 Orientación 3D**: Representación visual de los ejes (Roll, Pitch, Yaw) mediante un modelo 3D dinámico que responde a los datos del giroscopio.
* **📊 Gráficas Dinámicas**: Paneles en vivo para monitorear tendencias de altitud, temperatura y presión utilizando `pyqtgraph`.
* **🔗 Integración Webhook**: Envío automático de los datos procesados a una URL externa (n8n) para almacenamiento en la nube.
* **💻 Consola de Crudos**: Registro en tiempo real de los datos recibidos directamente del puerto serial.

---

## 🛠️ Requisitos e Instalación

### Dependencias
Asegúrate de tener instalado Python 3.9+ y las siguientes librerías:

```bash
pip install PyQt6 PyQt6-WebEngine pyqtgraph PyOpenGL pyserial requests numpy
