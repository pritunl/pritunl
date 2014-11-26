from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import logger
from pritunl import utils
from pritunl import event

import hashlib
import base64

def update():
    license = settings.app.license

    if not license:
        cur_sub_active = None
        cur_sub_plan = None
        settings.local.sub_active = False
        settings.local.sub_status = None
        settings.local.sub_plan = None
        settings.local.sub_amount = None
        settings.local.sub_period_end = None
        settings.local.sub_cancel_at_period_end = None
    else:
        for i in xrange(3):
            try:
                response = utils.request.get(
                    'https://app.pritunl.com/subscription',
                    json_data={
                        'license': license,
                        'version': settings.local.version_int,
                    },
                    timeout=max(settings.app.http_request_timeout, 15))

                # License key invalid
                if response.status_code == 470:
                    settings.app.license = None
                    settings.commit()
                    subscription_update()
                    return

                if response.status_code == 473:
                    raise ValueError(('Version %r not recognized by ' +
                        'subscription server') % settings.local.version_int)
                data = response.json()

                settings.local.sub_active = data['active']
                settings.local.sub_status = data['status']
                settings.local.sub_plan = data['plan']
                settings.local.sub_amount = data['amount']
                settings.local.sub_period_end = data['period_end']
                settings.local.sub_cancel_at_period_end = data[
                    'cancel_at_period_end']
                settings.local.sub_styles[data['plan']] = data['styles']
            except:
                if i < 2:
                    time.sleep(1)
                    continue
                logger.exception('Failed to check subscription status',
                    'subscription')
                settings.local.sub_active = False
                settings.local.sub_status = None
                settings.local.sub_plan = None
                settings.local.sub_amount = None
                settings.local.sub_period_end = None
                settings.local.sub_cancel_at_period_end = None

    response = collection.update({
        '_id': 'subscription',
        '$or': [
            {'active': {'$ne': settings.local.sub_active}},
            {'plan': {'$ne': settings.local.sub_plan}},
        ],
    }, {'$set': {
        'active': settings.local.sub_active,
        'plan': settings.local.sub_plan,
    }})
    if response['updatedExisting']:
        if settings.local.sub_active:
            if settings.local.sub_plan == 'premium':
                event.Event(type=SUBSCRIPTION_PREMIUM_ACTIVE)
            elif settings.local.sub_plan == 'enterprise':
                event.Event(type=SUBSCRIPTION_ENTERPRISE_ACTIVE)
            else:
                event.Event(type=SUBSCRIPTION_NONE_INACTIVE)
        else:
            if settings.local.sub_plan == 'premium':
                event.Event(type=SUBSCRIPTION_PREMIUM_INACTIVE)
            elif settings.local.sub_plan == 'enterprise':
                event.Event(type=SUBSCRIPTION_ENTERPRISE_INACTIVE)
            else:
                event.Event(type=SUBSCRIPTION_NONE_INACTIVE)

def dict():
    return {
        'active': settings.local.sub_active,
        'status': settings.local.sub_status,
        'plan': settings.local.sub_plan,
        'amount': settings.local.sub_amount,
        'period_end': settings.local.sub_period_end,
        'cancel_at_period_end': settings.local.sub_cancel_at_period_end,
    }

def update_license(license):
    settings.app.license = license
    settings.commit()
    update()
