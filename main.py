import sys
import json
import os
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QRadioButton , QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

load_dotenv()


class WeatherApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.header_label = QLabel("Enter city name:", self)

        self.city_name_input = QLineEdit(self)

        self.get_weather_button = QPushButton("Get Weather", self)

        self.celsius_button = QRadioButton("Celsius", self)
        self.fahrenheit_button = QRadioButton("Fahrenheit", self)
        self.celsius_button.setChecked(True)

        self.result_label = QLabel(self)

        self.network_manager = QNetworkAccessManager(self)

        self.initUI()


    def initUI(self):
        self.setWindowIcon(QIcon("weather_icon.png"))
        self.setWindowTitle("Weather App")
        self.setMinimumSize(500, 300)

        self.header_label.setMaximumHeight(40)

        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.city_name_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #Container widget
        main_widget = QWidget()

        #Layouts
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.header_label)
        vbox_layout.addWidget(self.city_name_input)
        vbox_layout.addWidget(self.get_weather_button)

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.celsius_button)
        hbox_layout.addWidget(self.fahrenheit_button)

        vbox_layout.addLayout(hbox_layout)
        vbox_layout.addWidget(self.result_label)

        #Add the Layouts to the Container Widget
        main_widget.setLayout(vbox_layout)

        #Put the Container Widget in the middle
        self.setCentralWidget(main_widget)

        self.header_label.setObjectName("header_label")
        self.result_label.setObjectName("result_label")

        self.setStyleSheet("""
            QLabel, QLineEdit, QPushButton, QRadioButton {
                font-family: calibri;
            }
            QLabel#header_label {
                font-size: 20px;
                background-color: hsl(178, 82%, 83%);
                border-radius: 10px;
            }
            QLabel#result_label {
                font-size: 35px;
                font-family: Segoe UI emoji;
            }
            QLineEdit {
                font-size: 24px;
                padding: 10px;
            }
            QPushButton {
                font-size: 15px;
                font-weight: bold;
            }
        """)

        self.city_name_input.returnPressed.connect(self.get_weather)
        self.get_weather_button.clicked.connect(self.get_weather)

        #To avoid double API requests
        self.celsius_button.toggled.connect(lambda: self.get_weather() if self.celsius_button.isChecked() else None)
        self.fahrenheit_button.toggled.connect(lambda: self.get_weather() if self.fahrenheit_button.isChecked() else None)

    #Does the request
    def get_weather(self):

        api_key = os.getenv("OPENWEATHERMAP_API_KEY", "OPENWEATHERMAP_API_KEY") #Use your own api key and pass it here
        city = self.city_name_input.text()

        if not city:
            self.display_error("Enter a city name first")
            return

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.network_response(reply))

    #Checks the response of the request
    def network_response(self, reply: QNetworkReply):
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
                error_type = reply.error()

                if status_code is not None:
                    error_message = self.http_error(status_code)
                    self.display_error(error_message)
                elif error_type == QNetworkReply.NetworkError.TimeoutError:
                    self.display_error("Timeout error:\nThe request timed out")
                else:
                    self.display_error("Connection error:\nCheck your internet connection")
                return

            raw_data = reply.readAll().data().decode("utf-8")
            data = json.loads(raw_data)

            temperature = self.get_temperature(data)
            weather_id = self.get_weather_id(data)
            weather_description = self.get_weather_description(data)
            weather_emoji = self.get_emoji(weather_id)

            self.result_label.setStyleSheet("font-size: 35px; font-family: Segoe UI emoji;")
            self.result_label.setText(f"{temperature} {weather_emoji}"
                                    f"\n{weather_description.title()}")
        except json.JSONDecodeError:
            self.display_error("Parsing error:\nInvalid data received from server")
        except Exception as e:
            self.display_error(f"An unexpected error occurred:\n{str(e)}")
        finally:
            reply.deleteLater()

    #To display errors
    def display_error(self, message):
        self.result_label.setStyleSheet("font-size: 30px;")
        self.result_label.setText(message)

    #To get temperature data and return it in (Celsius and Fahrenheit)
    def get_temperature(self, data):
        kelvin = data["main"]["temp"]
        if self.celsius_button.isChecked():
            temperature_c = kelvin - 273.15
            return f"{temperature_c:.2f}°C"
        else:
            temperature_f = (kelvin * 9/5) - 459.67
            return f"{temperature_f:.2f}°F"

    #To display specific error occurred
    @staticmethod
    def http_error(status_code):
        match status_code:
            case 400:
                return "Bad Request:\nPlease check your input"
            case 401:
                return "Unauthorized:\nInvalid API Key"
            case 403:
                return "Forbidden:\nAccess is denied"
            case 404:
                return "Not found:\nCity not found"
            case 500:
                return "Internal Server Error:\nPlease try again later"
            case 502:
                return "Bad Gateway:\nInvalid Response from the Server"
            case 503:
                return "Service Unavailable:\nServer is Down"
            case 504:
                return "Gateway Timeout:\nNo response from the server"
            case _:
                return f"HTTP error occurred:\nStatus code: {status_code}"

    #Get weather_id
    @staticmethod
    def get_weather_id(data):
        weather_id = data["weather"][0]["id"]
        return weather_id

    #Get weather_description
    @staticmethod
    def get_weather_description(data):
        weather_description = data["weather"][0]["description"]
        return weather_description

    #Generate emoji based on its weather_id
    @staticmethod
    def get_emoji(weather_id):

        if 200 <= weather_id <= 232:
            return "⛈"
        elif 300 <= weather_id <= 321:
            return "☁"
        elif 500 <= weather_id <= 531:
            return "🌧"
        elif 600 <= weather_id <= 622:
            return "🌨"
        elif 701 <= weather_id <= 741:
            return "🌫"
        elif weather_id == 762:
            return "🌋"
        elif weather_id == 771:
            return "💨"
        elif weather_id == 781:
            return "🌪"
        elif weather_id == 800:
            return "☀"
        elif 801 <= weather_id <= 804:
            return "⛅"
        else:
            return ""


if __name__ == '__main__':
    app = QApplication(sys.argv)
    weather_app = WeatherApp()
    weather_app.show()
    sys.exit(app.exec())