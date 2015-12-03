from pritunl.constants import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import logger
from pritunl import utils
from pritunl import event
from pritunl import mongo
from pritunl import messenger

def update():
    license = settings.app.license
    collection = mongo.get_collection('settings')

    if not license:
        settings.local.sub_active = False
        settings.local.sub_status = None
        settings.local.sub_plan = None
        settings.local.sub_amount = None
        settings.local.sub_period_end = None
        settings.local.sub_trial_end = None
        settings.local.sub_cancel_at_period_end = None
        settings.local.sub_url_key = None
    else:
        for i in xrange(2):
            try:
                response = utils.request.get(
                    'https://app.pritunl.com/subscription',
                    json_data={
                        'license': license,
                        'version': settings.local.version_int,
                    },
                    timeout=max(settings.app.http_request_timeout, 10),
                )

                # License key invalid
                if response.status_code == 470:
                    logger.warning('License key is invalid', 'subscription')
                    update_license(None)
                    update()
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
                settings.local.sub_trial_end = data['trial_end']
                settings.local.sub_cancel_at_period_end = data[
                    'cancel_at_period_end']
                settings.local.sub_url_key = data.get('url_key')
                settings.local.sub_styles[data['plan']] = data['styles']
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
                settings.local.sub_amount = None
                settings.local.sub_period_end = None
                settings.local.sub_trial_end = None
                settings.local.sub_cancel_at_period_end = None
                settings.local.sub_url_key = None
            break

    if settings.app.license_plan != settings.local.sub_plan and \
            settings.local.sub_plan:
        settings.app.license_plan = settings.local.sub_plan
        settings.commit()

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
    if settings.app.demo_mode:
        url_key = 'demo'
    else:
        url_key = settings.local.sub_url_key

    return {
        'active': settings.local.sub_active,
        'status': settings.local.sub_status,
        'plan': settings.local.sub_plan,
        'amount': settings.local.sub_amount,
        'period_end': settings.local.sub_period_end,
        'trial_end': settings.local.sub_trial_end,
        'cancel_at_period_end': settings.local.sub_cancel_at_period_end,
        'url_key': url_key,
    }

def update_license(license):
    settings.app.license = license
    settings.app.license_plan = None
    settings.commit()
    update()
    messenger.publish('subscription', 'updated')
