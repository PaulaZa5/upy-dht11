from umqtt.simple import MQTTClient
from uwebsrv.microWebSrv import MicroWebSrv
from machine import Pin
from dht import DHT11
from math import sqrt
from time import sleep

class History(object):
    def __init__(self, max_history):
        self.max_history = max_history
        self.items = []
    
    def append(self, elmnt):
        self.items.insert(0, elmnt)
        if len(self.items) > self.max_history:
            self.items.pop()
    
    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

t, h = 0, 0
MAX_HISTORY = 20
hist_t, hist_h = History(MAX_HISTORY), History(MAX_HISTORY)
max_t, max_h = -100, -100
min_t, min_h = 100, 100
mean_t, mean_h = 0, 0
var_t, var_h = 0, 0
std_t, std_h= 0, 0

def mean_variance_std(deq):
    sum = 0
    for elmnt in deq:
        sum = sum + elmnt
    mean = sum / len(deq)
    if len(deq) > 1:
        sum = 0
        for elmnt in deq:
            sum = sum + (elmnt-mean)**2
        var = sum / (len(deq) - 1)
        return mean, var, sqrt(var)
    else:
        return mean, 0, 0

server = 'test.mosquitto.org'
client_id = 'ESP32_DHT11_Sensor'
client = MQTTClient(client_id, server)
topic = b'cse1/train1/th'
try:
    client.connect()
except:
    pass

led = Pin(21, Pin.OUT, Pin.PULL_UP)
@MicroWebSrv.route('/dht')
def _httpHandlerDHTGet(httpClient, httpResponse):
    led.value(not led.value())
    data = 'Current Temperature: {0}&deg;C - Current Humidity: {1}%<br/>Temperature Maximum: {2}&deg;C - Humidity Maximum: {3}%<br/>Temperature Minimum: {4}&deg;C - Humidity Minimum: {5}%<br/>Temperature Mean: {6:3.4f} - Humidity Mean: {7:3.4f}<br/>Temperature Variance: {8:3.4f} - Humidity Variance: {9:3.4f}<br/>Temperature Standard Deviation: {10:3.4f} - Humidity Standard Deviation: {11:3.4f}<br/>'.format(t, h, max_t, max_h, min_t, min_h, mean_t, mean_h, var_t, var_h, std_t, std_h)
    httpResponse.WriteResponseOk(
        headers = ({'Cache-Control': 'no-cache'}),
        contentType = 'text/event-stream',
        contentCharset = 'UTF-8',
        content = 'data: {0}\n\n'.format(data))
routeHandlers = [ ( "/dht", "GET",  _httpHandlerDHTGet ) ]
srv = MicroWebSrv(routeHandlers=routeHandlers, webPath='/uwebsrv/www/')
srv.Start(threaded=True)

th = DHT11(Pin(0, Pin.IN, Pin.PULL_UP))

while True:
    sleep(2)
    try:
        th.measure()
        t, h = th.temperature(), th.humidity()
        if isinstance(t, int) and isinstance(h, int):
            if t > max_t:
                max_t = t
            elif t < min_t:
                min_t = t
            if h > max_h:
                max_h = h
            elif h < min_h:
                min_h = h
            hist_t.append(t)
            hist_h.append(h)
            mean_t, var_t, std_t = mean_variance_std(hist_t)
            mean_h, var_h, std_h = mean_variance_std(hist_h)

            msg = b'Current Temperature: {0}C\t\tCurrent Humidity: {1}%\nTemperature Maximum: {2}C\t\tHumidity Maximum: {3}%\nTemperature Minimum: {4}C\t\tHumidity Minimum: {5}%\nTemperature Mean: {6:3.4f}\t\tHumidity Mean: {7:3.4f}\nTemperature Variance: {8:3.4f}\t\tHumidity Variance: {9:3.4f}\nTemperature Standard Deviation: {10:3.4f}\tHumidity Standard Deviation: {11:3.4f}\n'.format(t, h, max_t, max_h, min_t, min_h, mean_t, mean_h, var_t, var_h, std_t, std_h)
            print(msg)

            try:
                client.publish(topic, msg)
            except:
                print('Failed to publish the message to the MQTT broker.\n')
        else:
            print('Invalid sensor reading.')
    except OSError:
        print('Failed to read sensor.')
