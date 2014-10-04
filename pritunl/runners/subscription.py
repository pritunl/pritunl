from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import event

def subscription_update():
    cur_sub_active = settings.local.sub_active
    license = settings.app.license
    if not license:
        settings.local.sub_active = False
        settings.local.sub_status = None
        settings.local.sub_amount = None
        settings.local.sub_period_end = None
        settings.local.sub_cancel_at_period_end = None
    else:
        try:
            response = utils.request.get(SUBSCRIPTION_SERVER,
                json_data={'license': license},
                timeout=max(settings.app.http_request_timeout, 10))
            # License key invalid
            if response.status_code == 470:
                settings.app.license = None
                settings.commit()
                #persist_db.remove('license')
                subscription_update()
                return
            data = response.json()
        except:
            logger.exception('Failed to check subscription status...')
            data = {}
        settings.local.sub_active = data.get('active', True)
        settings.local.sub_status = data.get('status', 'unknown')
        settings.local.sub_amount = data.get('amount')
        settings.local.sub_period_end = data.get('period_end')
        settings.local.sub_cancel_at_period_end = data.get(
            'cancel_at_period_end')
    if cur_sub_active is not None and \
            cur_sub_active != settings.local.sub_active:
        if settings.local.sub_active:
            event.Event(type=SUBSCRIPTION_ACTIVE)
        else:
            event.Event(type=SUBSCRIPTION_INACTIVE)
