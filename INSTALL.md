# Installation

Der Client ist in Micropython geschrieben, so dass ein ESP32 mit einem aktuellen MicroPython-Interpreter benötigt wird. Die Installation wird in der offiziellen Dokumentation [genauer besprochen](https://docs.micropython.org/en/latest/esp32/tutorial/intro.html). Die einzusetzende Firmware ist abhängig vom gekauften ESP32, typischerweise ist die stabile Firmware `esp32-20210418-v1.15.bin` oder `esp32-idf4-20210202-v1.14.bin` funktionsfähig.

Hat man den Interpreter installiert, hat man die Basis für MicroPython-Anwendungen aller Art, also auch dem Websocket-Client. Um den Websocket-Client zu installieren wird das Kommandozeilen-Tool `ampy` benötig. Eine Installationsanleitung kann man [im Github-Repository des Projektes abrufen](https://github.com/scientifichackers/ampy). 

Bevor man nun die Python-Dateien auf den ESP32 kopiert muss eine Konfiguration angelegt werden. Hierfür kopiert man die `./app/config_dist.py` zur `./app/config.py` und füllt alle Werte aus.

Mit einem installierten `ampy` und der fertigen Konfiguration kann man nun das Script `./update.sh` aufrufen, mit dem alle Python-Dateien auf den ESP32 kopiert werden. Wenn man den ESP32 nun kurz vom Strom nimmt sollte er sich im Anschluss automatisch verbinden. Wenn der ESP32 nicht unter dem Device Node `/dev/ttyUSB0` zu finden ist kann man den Device Node auch der `update.sh` übergeben: `update.sh /dev/ttyWHATEVER`.

## Debugging

Zur Fehlerbehebung kann es sich lohnen, die `boot.py` mit `ampy -p /dev/ttyUSB0 rm boot.py` zu löschen und die `boot.py` interaktiv zu starten: `ampy -p /dev/ttyUSB0 run boot.py`.

