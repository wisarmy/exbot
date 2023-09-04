 #!/bin/bash
 # download online data
 scp aws:workspace/exbot/exbot-py/logs/position.csv data
 python charts/position.py