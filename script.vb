//+------------------------------------------------------------------+
//|                                                  ML_Trader.mq5   |
//+------------------------------------------------------------------+
#property copyright ""
#property version   "1.0"
#property strict

CTrade trade;
input string Symbol = "EURUSD";
input ENUM_TIMEFRAMES TF = PERIOD_M5;
datetime lastCheck = 0;

//+------------------------------------------------------------------+
void OnTick()
{
   if(TimeCurrent() - lastCheck < PeriodSeconds(TF))
      return; // Check once per candle

   lastCheck = TimeCurrent();

   // Read ML predictions from file
   double predictions[];
   if(FileIsExist("predictions.csv"))
   {
      int file_handle = FileOpen("predictions.csv", FILE_READ|FILE_CSV);
      if(file_handle!=INVALID_HANDLE)
      {
         ArrayResize(predictions,3);
         for(int i=0; i<3; i++)
            predictions[i] = FileReadNumber(file_handle);
         FileClose(file_handle);

         double open_price = iOpen(Symbol,TF,1);
         double predicted_close = predictions[2];

         // Decision Logic
         if(predicted_close > open_price + _Point*10) // threshold
         {
            // CALL Option scenario (BUY)
            trade.Buy(0.1, Symbol);
         }
         else if(predicted_close < open_price - _Point*10)
         {
            // PUT Option scenario (SELL)
            trade.Sell(0.1, Symbol);
         }
      }
   }
}
//+------------------------------------------------------------------+