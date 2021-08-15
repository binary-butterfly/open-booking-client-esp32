import ujson


class Config:
    data = {}
    required_values = ['CLIENT_UID', 'WEBSOCKET_HOSTNAME', 'WEBSOCKET_PASSWORD', 'WIFI_NETWORK', 'WIFI_PASSWORD']

    def __init__(self):
        with open('/config.json') as config_file:
            self.data = ujson.load(config_file)
        missing_values = [value for value in self.required_values if value not in self.data]
        if len(missing_values):
            raise Exception('missing values: %s' % ', '.join(missing_values))

    @property
    def CLIENT_UID(self):
        return self.data.get('CLIENT_UID')

    @property
    def WEBSOCKET_HOSTNAME(self):
        return self.data.get('WEBSOCKET_HOSTNAME')

    @property
    def WEBSOCKET_PORT(self):
        return self.data.get('WEBSOCKET_PORT') or 443

    @property
    def WEBSOCKET_PATH(self):
        return self.data.get('WEBSOCKET_PATH') or '/connect/%s' % self.CLIENT_UID

    @property
    def WEBSOCKET_TLS(self):
        return self.data['WEBSOCKET_TLS'] if self.data.get('WEBSOCKET_TLS') is not None else True

    @property
    def WEBSOCKET_USER(self):
        return self.data.get('WEBSOCKET_USER') or self.CLIENT_UID

    @property
    def WEBSOCKET_PASSWORD(self):
        return self.data.get('WEBSOCKET_PASSWORD')

    @property
    def WIFI_NETWORK(self):
        return self.data.get('WIFI_NETWORK')

    @property
    def WIFI_PASSWORD(self):
        return self.data.get('WIFI_PASSWORD')

    @property
    def RESOURCE_UID(self):
        return self.data.get('RESOURCE_UID') or self.CLIENT_UID

    @property
    def LOCK_OPEN_PIN(self):
        return self.data.get('LOCK_OPEN_PIN') or 26

    @property
    def LOCK_CLOSE_PIN(self):
        return self.data.get('LOCK_CLOSE_PIN') or 27

    @property
    def DOOR_STATUS_PIN(self):
        return self.data.get('DOOR_STATUS_PIN') or 33

    @property
    def POWER_STATUS_PIN(self):
        return self.data.get('POWER_STATUS_PIN') or 34

    @property
    def DEBUG(self):
        return self.data['DEBUG'] if self.data.get('DEBUG') is not None else False

