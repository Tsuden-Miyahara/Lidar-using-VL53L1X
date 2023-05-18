#include <Wire.h>
#include "vl53l1_api.h"

#include <BTAddress.h>
#include <BTAdvertisedDevice.h>
#include <BTScan.h>
#include <BluetoothSerial.h>

#define SW_PIN 36

BluetoothSerial SerialBT;

VL53L1_Dev_t dev;  //Dev           : Device handleDev
VL53L1_DEV Dev = &dev;

int status, i, x, y, R;
float distance[25], INTdistance[64];


uint ROI_CONFIG_SIZE;
uint ROI_CONFIG_LENGTH;
// 16 ROI configurations
// VL53L1_UserRoi_t roiConfig[25];  //For definig 25 ROI configurations
VL53L1_UserRoi_t roiConfig[100];

uint8_t state = 0;
uint8_t stateUpdate() {
  state += 1;
  if (1 < state) {
    state = 0;
  }
  return state;
}

void setRoiConfig(uint roi_config_size) {
  ROI_CONFIG_SIZE = roi_config_size;
  ROI_CONFIG_LENGTH = roi_config_size * roi_config_size;
  i = 0;
  uint8_t seg = 16 / roi_config_size;
  for (y = 0; y < ROI_CONFIG_SIZE; y++) {
    for (x = 0; x < ROI_CONFIG_SIZE; x++) {
      roiConfig[i] = {
        seg * x,         (16 - seg * y),
        seg * (x + 1),   (16 - seg * (y + 1))
      };
      i++;
    }
  }
}

void setup() {
  pinMode(SW_PIN, INPUT);

  uint8_t byteData;
  uint16_t wordData;

  SerialBT.begin("VL53L1X_2");
  SerialBT.setTimeout(100);

  Wire.begin();
  Wire.setClock(400000);
  Serial.begin(115200);

  Dev->I2cDevAddr = 0x52;  //Declaring the I2C address of the sensor

  VL53L1_software_reset(Dev);

  VL53L1_RdByte(Dev, 0x010F, &byteData);
  //Serial.print(F("VL53L1X Model_ID: "));
  //Serial.println(byteData, HEX);
  VL53L1_RdByte(Dev, 0x0110, &byteData);
  //Serial.print(F("VL53L1X Module_Type: "));
  //Serial.println(byteData, HEX);
  VL53L1_RdWord(Dev, 0x010F, &wordData);
  //Serial.print(F("VL53L1X: "));
  //Serial.println(wordData, HEX);

  //Serial.println(F("Autonomous Ranging Test"));
  status = VL53L1_WaitDeviceBooted(Dev);
  status = VL53L1_DataInit(Dev);
  status = VL53L1_StaticInit(Dev);
  status = VL53L1_SetDistanceMode(Dev, VL53L1_DISTANCEMODE_SHORT);
  status = VL53L1_SetMeasurementTimingBudgetMicroSeconds(Dev, 50000);
  status = VL53L1_SetInterMeasurementPeriodMilliSeconds(Dev, 50);  // reduced to 50 ms from 500 ms in ST example
  status = VL53L1_StartMeasurement(Dev);

  if (status) {
    //Serial.println(F("VL53L1_StartMeasurement failed"));
    while (1)
      ;
  }

  // Creating 16 ROI definition
  setRoiConfig(4);
}

unsigned long temp_millis;

void loop_inner() {
  static VL53L1_RangingMeasurementData_t RangingData;

  status = VL53L1_WaitMeasurementDataReady(Dev);
  if (!status) {
    status = VL53L1_GetRangingMeasurementData(Dev, &RangingData);
    if (status == 0) {
      for (i = 0; i < ROI_CONFIG_LENGTH; i++) {
        // switching ROI configs
        status = VL53L1_SetUserROI(Dev, &roiConfig[i]);
        //    while (digitalRead(INT)); // slightly faster
        status = VL53L1_WaitMeasurementDataReady(Dev);
        if (!status) status = VL53L1_GetRangingMeasurementData(Dev, &RangingData);                   //4mS
        VL53L1_clear_interrupt_and_enable_next_range(Dev, VL53L1_DEVICEMEASUREMENTMODE_SINGLESHOT);  //2mS
        if (status == 0) distance[i] = RangingData.RangeMilliMeter + ((float) RangingData.RangeFractionalPart / 256);
      }
    }
    status = VL53L1_ClearInterruptAndStartMeasurement(Dev);
  } else {
    //Serial.print(F("error waiting for data ready: "));
    //Serial.println(status);
  }
  
  Serial.print(  "{\"size\": ");
  SerialBT.print("{\"size\": ");

  Serial.print(ROI_CONFIG_SIZE);
  SerialBT.print(ROI_CONFIG_SIZE);

  Serial.print(  ", ");
  SerialBT.print(", ");

  Serial.print(  "\"millis\": ");
  SerialBT.print("\"millis\": ");

  temp_millis = millis();
  Serial.print(temp_millis);
  SerialBT.print(temp_millis);

  Serial.print(  ", ");
  SerialBT.print(", ");
  
  Serial.print(  "\"data\": [");
  SerialBT.print("\"data\": [");

  for (i = 0; i < ROI_CONFIG_LENGTH; i++) {
    //Serial.print(i);
    Serial.print(distance[i]);
    SerialBT.print(distance[i]);

    if (i != ROI_CONFIG_LENGTH - 1) {
      Serial.print(", ");
      SerialBT.print(", ");
    }
  }
  Serial.println(  "]}");
  SerialBT.println("]}");
}

void loop() {
  if (digitalRead(SW_PIN) == LOW) {
    switch ( stateUpdate() ) {
      case 0:
        setRoiConfig(4);
        break;
      case 1:
        setRoiConfig(2);
        break;
      default:
        break;
    }
    while(digitalRead(SW_PIN) == LOW) loop_inner();
  }
  loop_inner();
  /*
  if (digitalRead(SW_PIN) == LOW) {
    Serial.println("ok");
    while(digitalRead(SW_PIN) == LOW);
  }
  */
}
