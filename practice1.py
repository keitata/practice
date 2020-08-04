import time 

    #定義
def main():
    sps30.ser.flushInput()
    sps30.ser.flushOutput()
    time.sleep(1)

    boolResult = sps30.stop(2)
    print('測定終了受信フレーム:{}'.format(boolResult))
    

    boolResult = sps30.start(1)
    print('測定終了受信フレーム:{}'.format(boolResult))

    boolResult = sps30.writeCleaning(1)
    print('測定終了受信フレーム:{}'.format(boolResult))


    boolResult = sps30.readCleaning(1)
    print('測定終了受信フレーム:{}'.format(boolResult))
    

    boolResult = sps30.startFanCleaning(1)
    print('測定終了受信フレーム:{}'.format(boolResult))
    
    

    
    while True:
        boolResult = sps30.read_values(10)
        print('測定終了受信フレーム:{}'.format(boolResult))
        if boolResult == True:
            sps30.createCSV(sps30.listReceiveFrame)
            time.sleep(1)
        
    sps30.stop(1)
    



if __name__ == '__main__':
    #Spsクラスのインスタンス生成
    sps30 = SPS30.Sps30("/dev/ttyAMA0")
    main()