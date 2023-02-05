from webserver import get_metadata_from_db
from webserver import modulate_status

import schedule
import time

def status_expiration():
    retrieved_metadata = get_metadata_from_db()
    status = retrieved_metadata.status
    if status == "busy":
        if expiration_time <= datetime.datetime.now():
            modulate_status(status, 1)

schedule.every(1).minutes.do(status_expiration)
while True:
    schedule.run_pending()
    time.sleep(1)

