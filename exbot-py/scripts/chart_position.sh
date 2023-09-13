 #!/bin/bash
 # download online data
 #export TAKE_PROFIT_FIX_PRICE_URATE=0.00786
 export TAKE_PROFIT_FIX_PRICE_URATE=0.005
 export STOP_LOSS_FIX_PRICE_URATE=0.00382
 scp aws:workspace/exbot/exbot-py/data/position.csv data
 python charts/position.py
