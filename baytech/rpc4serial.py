import serial
import re
import logging

_LOGGER = logging.getLogger(__name__)

RE_AveragePower = r'(Average Power):\s*(\d+\s*Watts)'
RE_TrueRmsVoltage = r'(True RMS Voltage):\s*(\d+.*\d*\s*Volts)'
RE_TrueRmsCurrent = r'(True RMS Current):\s*(\d+.*\d*\s*Amps)'
RE_MaximumDetected = r'(Maximum Detected):\s*(\d+.*\d*\s*Amps)'
RE_CircuitBreaker = r'(Circuit Breaker):\s*(\w+)'
RE_InternalTemperature = r'(Internal Temperature):\s*(\d+\.*\d*\s*C)'

RE_Outlet1 = r'1\)\.*\b(.*)\b\s*:\s*(\w*)'
RE_Outlet2 = r'2\)\.*\b(.*)\b\s*:\s*(\w*)'
RE_Outlet3 = r'3\)\.*\b(.*)\b\s*:\s*(\w*)'
RE_Outlet4 = r'4\)\.*\b(.*)\b\s*:\s*(\w*)'
RE_Outlet5 = r'5\)\.*\b(.*)\b\s*:\s*(\w*)'
RE_Outlet6 = r'6\)\.*\b(.*)\b\s*:\s*(\w*)'
RE_Outlet7 = r'7\)\.*\b(.*)\b\s*:\s*(\w*)'
RE_Outlet8 = r'8\)\.*\b(.*)\b\s*:\s*(\w*)'

#
# Example from BayTech RPC-4 serial output
#
# Unit ID: my-power

# True RMS Current:   0.9 Amps
# Maximum Detected:   2.8 Amps

# Internal Temperature:  33.5 C

# Circuit Breaker: Off 

# 1)...port01    : On 
# 2)...port02    : On 
# 3)...port03    : On 
# 4)...port04    : On 
# 5)...port05    : On 
# 6)...port06    : On 
# 7)...port07    : On 
# 8)...port08    : On 

# Type "Help" for a list of commands

class RPC4_NC(object):
    """ Controls an BayTech RPC4-NC PDU.
    """
    def __init__(self, device=None, baud=9600, timeout=5000, xonxoff=False, rtscts=False, dsrdtr=False, command_prompt='>'):
        self.device = device
        self.baud = baud
        self.timeout = timeout
        self.xonxoff = xonxoff
        self.rtscts = rtscts
        self.dsrdtr = dsrdtr
        self.command_prompt = command_prompt.encode('UTF-8')
        self.serial = None
        self.connected = False

    def connect(self):
        self.serial = serial.Serial(self.device, baudrate=self.baud, timeout=self.timeout, xonxoff=self.xonxoff, rtscts=self.rtscts, dsrdtr=self.dsrdtr)
        self.serial.write('\r\n'.encode('UTF-8'))
        prompt = self.serial.read_until(self.command_prompt, self.timeout)

        if self.command_prompt in prompt:
            self.connected = True
            return True, None
        else:
            return False, 'Cannot connect to %s' % (self.device)

    def state(self):
        print(f'Connected: {self.connected}')
        if self.serial is not None:
            print(f'self.serial is not None')
            return True
        else:
            print(f'self.serial is None')
            return False

    def close(self):
        if self.serial is not None and self.connected:
            self.serial.close()

    def _parseStatus(self, raw_status):
        status = {}

        if raw_status is None:
            return status

        raw_status = raw_status.decode("utf-8")

        _LOGGER.debug('Raw Status:\n%s' % ( raw_status ) )

        #AveragePower
        m= re.findall(RE_AveragePower, raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            status[key] = value
        else:
            _LOGGER.debug( 'No match' )


        #RE_TrueRmsVoltage
        m = re.findall(RE_TrueRmsVoltage,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            status[key] = value
        else:
            _LOGGER.debug( 'No match' )

        #RE_TrueRmsCurrent
        m = re.findall(RE_TrueRmsCurrent,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            status[key] = value.replace(" Amps", "")
        else:
            _LOGGER.debug( 'No match' )

        #RE_MaximumDetected
        m = re.findall(RE_MaximumDetected,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            status[key] = value.replace(" Amps", "")
        else:
            _LOGGER.debug( 'No match' )

        #RE_CircuitBreaker
        m = re.findall(RE_CircuitBreaker,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            status[key] = value
        else:
            _LOGGER.debug( 'No match' )

        #RE_InternalTemperature
        m = re.findall(RE_InternalTemperature,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            status[key] = value
        else:
            _LOGGER.debug( 'No match' )

        outlets = {}

        #RE_Outlet1
        m = re.findall(RE_Outlet1,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            if key=='':
                key = 'Outlet 1'
            outlets['1'] = {key: value}
        else:
            outlets['1'] = {}
            _LOGGER.debug( 'No match' )

        #RE_Outlet2
        m = re.findall(RE_Outlet2,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            if key=='':
                key = 'Outlet 2'
            outlets['2'] = {key: value}
        else:
            outlets['2'] = {}
            _LOGGER.debug( 'No match' )

        #RE_Outlet3
        m = re.findall(RE_Outlet3,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            if key=='':
                key = 'Outlet 3'
            outlets['3'] = {key: value}
        else:
            outlets['3'] = {}
            _LOGGER.debug( 'No match' )

        #RE_Outlet4
        m = re.findall(RE_Outlet4,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            if key=='':
                key = 'Outlet 4'
            outlets['4'] = {key: value}
        else:
            outlets['4'] = {}
            _LOGGER.debug( 'No match' )

        #RE_Outlet5
        m = re.findall(RE_Outlet5,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            if key=='':
                key = 'Outlet 5'
            outlets['5'] = {key: value}
        else:
            outlets['5'] = {}
            _LOGGER.debug( 'No match' )

        #RE_Outlet6
        m = re.findall(RE_Outlet6,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            if key=='':
                key = 'Outlet 6'
            outlets['6'] = {key: value}
        else:
            outlets['6'] = {}
            _LOGGER.debug( 'No match' )
        status['outlets'] = outlets

        #RE_Outlet7
        m = re.findall(RE_Outlet7,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            if key=='':
                key = 'Outlet 7'
            outlets['7'] = {key: value}
        else:
            outlets['7'] = {}
            _LOGGER.debug( 'No match' )

        #RE_Outlet8
        m = re.findall(RE_Outlet8,raw_status)
        if m and len(m) >=1:
            _LOGGER.debug( '%s' % (m) )
            key,value = m[0]
            if key=='':
                key = 'Outlet 8'
            outlets['8'] = {key: value}
        else:
            outlets['8'] = {}
            p_LOGGER.debug( 'No match' )

        status['outlets'] = outlets
        return status


    def getStatus(self, outlet=-1):
        if self.serial is not None and self.connected:
            self.serial.write(b'\r')
            response = self.serial.read_until(self.command_prompt, self.timeout)

            status = self._parseStatus(response)

            if outlet < 1:
                #Return All
                return status
            elif outlet <=8:
                key = '%s' % (outlet)
                return status['outlets'][key]
            else :
                return {}

        else:
            return {}

    def turnOn(self, outlet=-1):
        if self.serial is not None and self.connected:
            if outlet >=1 and outlet <=8:
                port_on = f'On {outlet}\r\n'.encode('UTF-8')
                self.serial.write(port_on)
                response = self.serial.read_until(self.command_prompt, self.timeout)

    def turnOnAll(self):
        if self.serial is not None and self.connected:
            self.turnOn(1)
            self.turnOn(2)
            self.turnOn(3)
            self.turnOn(4)
            self.turnOn(5)
            self.turnOn(6)
            self.turnOn(7)
            self.turnOn(8)

    def turnOff(self, outlet=-1):
        if self.serial is not None and self.connected:
            if outlet >=1 and outlet <=8:
                port_off = f'Off {outlet}\r\n'.encode('UTF-8')
                self.serial.write(port_off)
                response = self.serial.read_until(self.command_prompt, self.timeout)

    def turnOffAll(self):
        if self.serial is not None and self.connected:
            self.turnOff(1)
            self.turnOff(2)
            self.turnOff(3)
            self.turnOff(4)
            self.turnOff(5)
            self.turnOff(6)
            self.turnOff(7)
            self.turnOff(8)
