import socket,select,pickle,time
#This file will be removed in future and is only for testing
ip = "127.0.0.1"
uport = 3745
tport = 3746

tsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
tsock.settimeout(24)
tsock.connect((ip,tport))
print("TCP connected")
usock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

tsock.sendall(pickle.dumps(["Ping","Hello!"]))
print("Sending TCP ping")
usock.sendto(pickle.dumps(["Ping2","Hello!2"]),(ip,uport))
print("Sending UDP ping")

sTime = 1/30
stress = time.time()+sTime
rec = 0
timeInt = time.time()+sTime

while True:
    if time.time()>timeInt:
        print(str(rec)+" out of "+str(1/sTime)+" received")
        rec = 0
        timeInt = time.time()+1
    if time.time()>stress:
        stress = time.time()+sTime
        tsock.sendall(pickle.dumps(["Pong"]))
    #UDP socket
    read,write,err = select.select([usock],[],[],0)
    for sock in read:
        if sock == usock:
            data,con = sock.recvfrom(4096)
            print("Got (UDP)",pickle.loads(data))
    #TCP socket
    read,write,err = select.select([tsock],[],[],0)
    for sock in read:
        if sock == tsock:
            dataRaw = sock.recv(4096)
            data = pickle.loads(dataRaw)
            if data=="p": #A ping was received
                tsock.sendall(pickle.dumps("p"))
            else:
                #print("Got (TCP)",data)
                rec += 1
