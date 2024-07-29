from pritunl.constants import *
from pritunl.helpers import *
from pritunl.exceptions import *
from pritunl import settings
from pritunl import logger
from pritunl import utils
from pritunl import event
from pritunl import mongo
from pritunl import messenger

import requests
import base64

def x(a):
    return base64.b64decode(a).decode()

def update():
    license = settings.app.license
    collection = mongo.get_collection('settings')

    if not settings.app.id:
        settings.app.id = utils.random_name()
        settings.commit()

    if not license:
        settings.local.sub_active = False
        settings.local.sub_status = None
        settings.local.sub_plan = None
        settings.local.sub_quantity = None
        settings.local.sub_amount = None
        settings.local.sub_period_end = None
        settings.local.sub_trial_end = None
        settings.local.sub_cancel_at_period_end = None
        settings.local.sub_balance = None
        settings.local.sub_portal_url = None
        settings.local.sub_premium_buy_url = None
        settings.local.sub_enterprise_buy_url = None
        settings.local.sub_url_key = None
    else:
        for i in range(2):
            try:
                url = x(b'aHR0cHM6Ly9hcHAucHJpdHVubC5jb20vc3Vic2NyaXB0aW9u')

                response = requests.get(
                    url,
                    json={
                        x(b'aWQ='): settings.app.id,
                        x(b'bGljZW5zZQ=='): license,
                        x(b'dmVyc2lvbg=='): settings.local.version_int,
                    },
                    timeout=max(settings.app.http_request_timeout, 10),
                )

                # License key invalid
                if response.status_code == 470:
                    raise ValueError('License key is invalid')

                if response.status_code == 473:
                    raise ValueError(('Version %r not recognized by ' +
                        'subscription server') % settings.local.version_int)

                data = response.json()

                settings.local.sub_active = data[x(b'YWN0aXZl')]
                settings.local.sub_status = data[x(b'c3RhdHVz')]
                settings.local.sub_plan = data[x(b'cGxhbg==')]
                settings.local.sub_quantity = data[x(b'cXVhbnRpdHk=')]
                settings.local.sub_amount = data[x(b'YW1vdW50')]
                settings.local.sub_period_end = data[x(b'cGVyaW9kX2VuZA==')]
                settings.local.sub_trial_end = data[x(b'dHJpYWxfZW5k')]
                settings.local.sub_cancel_at_period_end = \
                    data[x(b'Y2FuY2VsX2F0X3BlcmlvZF9lbmQ=')]
                settings.local.sub_balance = data.get(x(b'YmFsYW5jZQ=='))
                settings.local.sub_portal_url = \
                    data.get(x(b'cG9ydGFsX3VybA=='))
                settings.local.sub_premium_buy_url = \
                    data.get(x(b'cHJlbWl1bV9idXlfdXJs'))
                settings.local.sub_enterprise_buy_url = \
                    data.get(x(b'ZW50ZXJwcmlzZV9idXlfdXJs'))
                settings.local.sub_url_key = data.get(x(b'dXJsX2tleQ=='))
                settings.local.sub_styles[data[x(b'cGxhbg==')]] = \
                    data[x(b'c3R5bGVz')]
            except:
                if i < 1:
                    logger.exception('Failed to check subscription status',
                        'subscription, retrying...')
                    time.sleep(1)
                    continue
                logger.exception('Failed to check subscription status',
                    'subscription')
                settings.local.sub_active = False
                settings.local.sub_status = None
                settings.local.sub_plan = None
                settings.local.sub_quantity = None
                settings.local.sub_amount = None
                settings.local.sub_period_end = None
                settings.local.sub_trial_end = None
                settings.local.sub_cancel_at_period_end = None
                settings.local.sub_balance = None
                settings.local.sub_url_key = None
            break

    if settings.app.license_plan != settings.local.sub_plan and \
            settings.local.sub_plan:
        settings.app.license_plan = settings.local.sub_plan
        settings.commit()

    response = collection.update_one({
        '_id': 'subscription',
        '$or': [
            {'active': {'$ne': settings.local.sub_active}},
            {'plan': {'$ne': settings.local.sub_plan}},
        ],
    }, {'$set': {
        'active': settings.local.sub_active,
        'plan': settings.local.sub_plan,
    }})
    if bool(response.modified_count):
        if settings.local.sub_active:
            if settings.local.sub_plan == 'premium':
                event.Event(type=SUBSCRIPTION_PREMIUM_ACTIVE)
            elif settings.local.sub_plan == 'enterprise':
                event.Event(type=SUBSCRIPTION_ENTERPRISE_ACTIVE)
            elif settings.local.sub_plan == 'enterprise_plus':
                event.Event(type=SUBSCRIPTION_ENTERPRISE_PLUS_ACTIVE)
            else:
                event.Event(type=SUBSCRIPTION_NONE_INACTIVE)
        else:
            if settings.local.sub_plan == 'premium':
                event.Event(type=SUBSCRIPTION_PREMIUM_INACTIVE)
            elif settings.local.sub_plan == 'enterprise':
                event.Event(type=SUBSCRIPTION_ENTERPRISE_INACTIVE)
            elif settings.local.sub_plan == 'enterprise_plus':
                event.Event(type=SUBSCRIPTION_ENTERPRISE_PLUS_INACTIVE)
            else:
                event.Event(type=SUBSCRIPTION_NONE_INACTIVE)

    return True

def dict():
    if settings.app.demo_mode:
        url_key = 'demo'
    else:
        url_key = settings.local.sub_url_key

    if settings.app.demo_mode:
        portal_url = 'demo'
    else:
        portal_url = settings.local.sub_portal_url

    if settings.app.demo_mode:
        premium_buy_url = 'demo'
    else:
        premium_buy_url = settings.local.sub_premium_buy_url

    if settings.app.demo_mode:
        enterprise_buy_url = 'demo'
    else:
        enterprise_buy_url = settings.local.sub_enterprise_buy_url

    return {
        'active': settings.local.sub_active,
        'status': settings.local.sub_status,
        'plan': settings.local.sub_plan,
        'quantity': settings.local.sub_quantity,
        'amount': settings.local.sub_amount,
        'period_end': settings.local.sub_period_end,
        'trial_end': settings.local.sub_trial_end,
        'cancel_at_period_end': settings.local.sub_cancel_at_period_end,
        'balance': settings.local.sub_balance,
        'portal_url': portal_url,
        'premium_buy_url': premium_buy_url,
        'enterprise_buy_url': enterprise_buy_url,
        'url_key': url_key,
    }

def update_license(license):
    settings.app.license = license
    settings.app.license_plan = None
    settings.commit()
    valid = update()
    messenger.publish('subscription', 'updated')
    if not valid:
        raise LicenseInvalid('License key is invalid')
