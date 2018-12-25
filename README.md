# autocall
Autocall via Asterisk using DB for call initialization. 
Script dialer.py parse table "to_parse", get telephone number to call and record number to play, then call to this number, play a record, wait for digit input (DTMF) and make a record about the results of the call to "to_read" table". If the callee don't make any choise - script redirects call to call center.

Script works with two tables in DB:
1) "to_parse" (`to_parse`(`id`, `timestamp`, `number`, `code`, `record`)) - put there number, code = 0 and record number to play. 
2) "to_read" (`to_read`(`id`, `timestamp`, `number`, `code`, `record`, `status`)) - script moves here the result of the call:
- code = 1, status = Busy - busy / underdial
- code = 2, status = Hangup - the client answered the call, but didn't make a choice, and ended the call within 5 seconds (billsec <5 sec)
- code = 3, status = Answer - the client answered the call and made a choice by pressing the key (by DTMF)
- code = 4, status = Answer - the client answered the call, did not make a choice within 5 seconds, he was offered again to make a choice, again didn't make a choice, redirected him to call center
- code = 4, status = Declined - the same as the previous item, but the client didn't wait for the connection with the CC operator

How to use:
0) Don't forget to create AMI user, replace all needeble variables in dialer.py and rellocate.py scripts and put records to var/lib/asterisk/sounds/, like 1.wav, 2.wav, etc.
1) Run script dialer.py with python3.4 interpreter ( you can run it in screen or systemctl for example)
2) Put telephone number, code = 0 and record number to play - INSERT INTO `to_parse`(`number`, `code`, `record`) VALUES ('0671231122',0,1) - call 0671231122 and play var/lib/asterisk/sounds/1.wav
3) Script will parse this record in DB, place a call to Asterisk using AMI (originate application) to extension 9004, then Asterisk make a call, play a voice record and call script rellocate.py to make a record about results of the call to table "to_read" in DB. See extensions_git.conf.
4) Script writes logs to /var/log/dialer.log and /var/log/rellocate.log
