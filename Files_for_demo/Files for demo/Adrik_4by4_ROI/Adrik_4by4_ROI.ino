#include <Wire.h>
#include "vl53l1_api.h"

#include <BTAddress.h>
#include <BTAdvertisedDevice.h>
#include <BTScan.h>
#include <BluetoothSerial.h>

#include <math.h>

#define SW_PIN 36
#define MAX_STATE_LEVEL 3

bool debug_mode = false;

BluetoothSerial SerialBT;

VL53L1_Dev_t dev;  //Dev           : Device handleDev
VL53L1_DEV Dev = &dev;

int status, i, x, y, R;
float distance[25], INTdistance[64];


uint ROI_CONFIG_SIZE_X, ROI_CONFIG_SIZE_Y;
uint ROI_CONFIG_LENGTH;
// 16 ROI configurations
// VL53L1_UserRoi_t roiConfig[25];  //For definig 25 ROI configurations
VL53L1_UserRoi_t roiConfig[25];

uint8_t state = 0;
uint8_t _stateUpdate() {
  state += 1;
  if (MAX_STATE_LEVEL < state) {
    state = 0;
  }
  return state;
}
void stateUpdate() {
  switch ( _stateUpdate() ) {
    case 0:
      setRoiConfig(4, 4);
      break;
    case 1:
      setRoiConfig(2, 2);
      break;
    case 2:
      setRoiConfig(1, 2);
      break;
    case 3:
      setRoiConfig(2, 1);
      break;
    default:
      break;
  }
  delay(10);
}

void setRoiConfig(uint roi_size_x, uint roi_size_y) {
  ROI_CONFIG_SIZE_X = roi_size_x;
  ROI_CONFIG_SIZE_Y = roi_size_y;
  ROI_CONFIG_LENGTH = roi_size_x * roi_size_y;
  i = 0;
  uint8_t seg_x = 16 / ROI_CONFIG_SIZE_X;
  uint8_t seg_y = 16 / ROI_CONFIG_SIZE_Y;
  for (y = 0; y < ROI_CONFIG_SIZE_Y; y++) {
    for (x = 0; x < ROI_CONFIG_SIZE_X; x++) {
      /*roiConfig[i] = {
        seg_x * x,               15 - (seg_x * y),    // Top-Left
        (seg_x * (x + 1) - 1),   15 - (seg_y * y + 3) // Bottom-Right
      };*/
      VL53L1_UserRoi_t uROI;

      uROI.TopLeftX  = seg_x * x;
      uROI.TopLeftY  = 15 - (seg_y * y);

      uROI.BotRightX = seg_x * (x + 1) - 1;
      uROI.BotRightY = 15 - (seg_y * (y + 1) - 1);
      
      roiConfig[i] = uROI;
      i++;
    }
  }
  
}

void pad(uint value, uint8_t length = 4) {  
  uint8_t dig = log10(value) + 1;
  if (!value) dig = 1;
  for (uint8_t x = 0; x < length - dig; x++) Serial.print(" ");
  Serial.print(value);
}

void setup() {
  pinMode(SW_PIN, INPUT);

  if (digitalRead(SW_PIN) == LOW) {
    debug_mode = true;
    delay(1000);
    Serial.println("Debug mode");
  }

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
  if (debug_mode) {
    Serial.print(F("VL53L1X Model_ID: "));
    Serial.println(byteData, HEX);
  }
  VL53L1_RdByte(Dev, 0x0110, &byteData);
  if (debug_mode) {
    Serial.print(F("VL53L1X Module_Type: "));
    Serial.println(byteData, HEX);
  }
  VL53L1_RdWord(Dev, 0x010F, &wordData);
  if (debug_mode) {
    Serial.print(F("VL53L1X: "));
    Serial.println(wordData, HEX);
  }

  //Serial.println(F("Autonomous Ranging Test"));
  status = VL53L1_WaitDeviceBooted(Dev);
  status = VL53L1_DataInit(Dev);
  status = VL53L1_StaticInit(Dev);
  status = VL53L1_SetDistanceMode(Dev, VL53L1_DISTANCEMODE_SHORT);
  status = VL53L1_SetMeasurementTimingBudgetMicroSeconds(Dev, 75000);
  status = VL53L1_SetInterMeasurementPeriodMilliSeconds(Dev, 75);  // reduced to 50 ms from 500 ms in ST example
  status = VL53L1_StartMeasurement(Dev);

  if (status) {
    //Serial.println(F("VL53L1_StartMeasurement failed"));
    while (1)
      ;
  }

  // Creating 16 ROI definition
  setRoiConfig(4, 4);
}

unsigned long temp_millis;
void loop_inner() {
  static VL53L1_RangingMeasurementData_t RangingData;

  status = VL53L1_WaitMeasurementDataReady(Dev);
  if (!status) {
    status = VL53L1_GetRangingMeasurementData(Dev, &RangingData);
    if (status == 0) {
      Serial.println("");
      for (i = 0; i < ROI_CONFIG_LENGTH; i++) {
        // switching ROI configs
        status = VL53L1_SetUserROI(Dev, &roiConfig[i]);
        status = VL53L1_WaitMeasurementDataReady(Dev);
        if (!status) status = VL53L1_GetRangingMeasurementData(Dev, &RangingData);
        VL53L1_clear_interrupt_and_enable_next_range(Dev, VL53L1_DEVICEMEASUREMENTMODE_SINGLESHOT);
        distance[i] = -9999.9;
        if (status == 0) {
          distance[i] = RangingData.RangeMilliMeter;

          if (debug_mode) {
            pad(RangingData.RangeMilliMeter, 4);
            Serial.print(" -> ROI: ");
            Serial.print(" Top-Left  [X,Y]: [");
            pad(roiConfig[i].TopLeftX, 2);
            Serial.print(", ");
            pad(roiConfig[i].TopLeftY, 2);
            Serial.println("],");
            Serial.print("              Bot-Right [X,Y]: [");
            pad(roiConfig[i].BotRightX, 2);
            Serial.print(", ");
            pad(roiConfig[i].BotRightY, 2);
            Serial.println("]");
          }
        }
      }
    }
    status = VL53L1_ClearInterruptAndStartMeasurement(Dev);
  } else {
    //Serial.print(F("error waiting for data ready: "));
    //Serial.println(status);
  }
  
  temp_millis = millis();

  Serial.print("{\"size_x\": ");
  Serial.print(ROI_CONFIG_SIZE_X);
  Serial.print(", \"size_y\": ");
  Serial.print(ROI_CONFIG_SIZE_Y);
  Serial.print(", \"millis\": ");
  Serial.print(temp_millis);
  Serial.print(", \"data\": [");
  
  SerialBT.print("{\"size_x\": ");
  SerialBT.print(ROI_CONFIG_SIZE_X);
  SerialBT.print(", \"size_y\": ");
  SerialBT.print(ROI_CONFIG_SIZE_Y);
  SerialBT.print(", \"millis\": ");
  SerialBT.print(temp_millis);
  SerialBT.print(", \"data\": [");

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
    stateUpdate();
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
