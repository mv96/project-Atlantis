"""
Remember to start the daemon with the command
'sudo pigpiod' before running this script. It
needs to be restarted every time your pi
is restarted.
"""
##### Mqtt client ######
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import serial
import time
import pigpio
import DHT22
from time import sleep
from picamera import PiCamera
cam_duration=0
Broker = "192.168.150.11"  # ip of the broker and the server 

sub_topic = "sensor/instructions"    # receive messages on this topic

pub_topic = "sensor/data"       # send messages to this topic
##########mqtt functions##############
# when connecting to mqtt do this;

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(sub_topic)

# when receiving a mqtt message do this;

def on_message(client, userdata, message):
    print("message received ="+"\n",str(message.payload.decode("utf-8")))
    print("message topic =",message.topic)
    print("message qos =",message.qos)
    print("message retain flags =",message.retain)
    if("exit"==str(message.payload.decode("utf-8"))):
        global control
        control ="exit"
    elif("exit_ir"==str(message.payload.decode("utf-8"))):
        global control
        control ="exit_ir"
    elif("cam"==str(message.payload.decode("utf-8"))[0:3]):
        global control
        global cam_duration
        cam_duration=str(message.payload.decode("utf-8"))[3:5]
        cam_duration=int(cam_duration)
        control ="camera"
    else:
        control=''
    

def on_publish(mosq, obj, mid):
    print("mid: " + str(mid))

    

#client = mqtt.Client()
#client.on_connect = on_connect
#client.on_message = on_message
#client.connect(Broker, 1883, 60)
#client.loop_start()
################################

# Initiate GPIO for pigpio
pi = pigpio.pi()
# Setup the sensor
sensor_pin=27
dht22 = DHT22.sensor(pi, sensor_pin) # use the actual GPIO pin #name
dht22.trigger()
led_1=17 #blue led
led_2=22 #red led
stop_led=23 #stop led
pi.set_mode(led_1, pigpio.OUTPUT) #led to light when temp is sf 
pi.set_mode(led_2, pigpio.OUTPUT) #led to light when bulb isn't
status='default'
threshold= 30
# We want our sleep time to be above 2 seconds.
sleepTime = 3
control=''
mac_id="_ id=00:1B:44:11:3A:B7"
def readDHT22():
    # Get a new reading
    dht22.trigger()
    # Save our values
    humidity  = '%.2f' % (dht22.humidity())
    temp = '%.2f' % (dht22.temperature())
    return (humidity, temp)


while True:
    global control
    if 'exit' not in control:
        pi.write(stop_led,0)
    ####################temp_sensor#########################
    humidity, temperature = readDHT22()
    humidity_m="Humidity=" + humidity + mac_id
    temperature_m="Temperature=" + temperature +mac_id
    #print(humidity_m)
    #print(temperature_m)
    temperature=float(temperature)
    if (temperature>threshold and (control != 'exit')):
        status='UnSafe'
        pi.write(led_1,0)
        pi.write(led_2,1)
    elif((temperature<threshold) and (control != 'exit')):
        status='Safe'
        pi.write(led_2,0)
        pi.write(led_1,1)    
    #print (status)
    ####################ir_sensor#########################
    ser = serial.Serial('/dev/ttyACM0', 9600)
    input = ser.readline()
    input=str(input)
    input=input[2]+input[3]
    ir_m=("distance="+input+mac_id)
    #############################################
    print('£££££££££')
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(Broker, 1883, 60)
    client.loop_start()
    ###############     sending  the data  #############################
    print("subscribing.......")
    client.subscribe("sensor")
    if(control!='exit'):
        print("publishing.......")
        client.publish("sensor/t", str(temperature_m))
        #sleep(2)
        #client.publish("sensors", str(humidity_m))
        #sleep(1)
        client.publish("sensor/d", str(ir_m))
        #sleep(2)
    client.publish("cam05", "exit")
    sleep(2)
    if(control=="exit"):
        print ("sending stop signal.......")
        pi.write(led_2,0)
        pi.write(led_1,0)
        pi.write(stop_led,1)
        continue
    ################  camera code ################
    if(control=='camera'):
        camera=PiCamera()
        camera.start_preview()
        for i in range(3):
            sleep(1)
            camera.capture('/home/pi/data_set/image%s.jpg' % i)
        sleep(cam_duration)
        camera.stop_preview()
        continue
        
#client.loop_stop()
    
##    time.sleep(60)
